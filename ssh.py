#!/usr/bin/env python3
import argparse
import getpass
import os.path
import paramiko
import select
import socket
import sys
from paramiko.py3compat import u

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False

import scp


class Client(paramiko.SSHClient):

    def __init__(self, host):
        super().__init__()
        self.load_system_host_keys()
        self.host = host
        # Add missing host keys by default, for now
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    
    # Would be connect() but I don't want to mess up paramiko's method atm
    def client_connect(self):

        print(f"Connecting: {self.user}@{self.host}:{self.port}")

        # Try to authenticate 3 times if using password
        attempts = 3 
        for i in range(attempts):
            try:
                self.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                key_filename=self.keys,
                look_for_keys=self.key_lookup
                )
                break
            except paramiko.ssh_exception.AuthenticationException as err:
                if not self.use_password:
                    raise err
                sys.stderr.write("%s\n" % err)
                if i == 2:
                    exit()
                self.password = getpass.getpass()
        
        print("Connected!")
        

    # Create Clients from command line arguments
    @classmethod
    def from_options(cls, sftp=False):

        # Read basic options from command-line
        args = parse_options(sftp=sftp)
        if sftp:
            user, host, port, resource = scp.parse_scp_host(args)
        else:
            user, host, port = parse_host_string(args)

        # Instantiate Client
        client = cls(host)
        # Read configs to set defaults
        client.parse_config()

        # Override config with any command-line options
        if user:
            client.user = user
        if port:
            client.port = port
        
        if args.password:
            client.password = args.password
            client.use_password = True
        elif args.passfile:
            client.password = read_passfile(args.passfile)
        
        if args.identity_file:
            client.keys = [args.identity_file]
        
        # scp things
        if sftp:
            remote_resource, local_resource = scp.find_remote(args.host, args.destination)
            if remote_resource == args.host:
                client.scp_method = "get"
            else:
                client.scp_method = "put"
            client.remote_resource = remote_resource
            client.local_resource = local_resource
            client.resource = resource

        return client

        

    # Initialized self.config (rhost's paramiko.config.SSHConfigDict)
    def get_config(self, config_file=None):
        config = paramiko.config.SSHConfig()
        
        # Normalize paths 
        if not config_file:
            cfg = "~/.ssh/config"
        else:
            cfg = config_file
        cfg = os.path.expandvars(cfg)
        cfg = os.path.expanduser(cfg)
        
        # Parse, and be chill if no config was specified
        try:
            with open(cfg) as f:
                config.parse(f)
        except FileNotFoundError as err:
            if config_file:
                raise err
            else:
                try:
                    with open("/etc/ssh/ssh_config") as f:
                        config.parse(f)
                except FileNotFoundError as err:
                    sys.stderr.write("No config files found!\n%s" % err)
        
        self.config = config.lookup(self.host)
    

    def parse_config(self, config_file=None):

        self.password = None

        # Read config file if haven't already
        if not hasattr(self, 'config'):
            self.get_config(config_file)
        
        # User
        if self.config.get("user", False):
            self.user = self.config['user']
        else:
            self.user = getpass.getuser()
        # Port
        if self.config.get("port", False):
            self.port = self.config.as_int("port")
        else:
            self.port = 22
        # Identity files
        if self.config.get("identityfile", False):
            self.keys = self.config['identityfile']
            self.key_lookup = False
        else:
            self.keys = None
            if self.config.get("pubkeyauthentication", False):
                self.key_lookup = self.config.as_bool('pubkeyauthentication')
            else:
                self.key_lookup = True
        # Passwords
        if self.config.get("passwordauthentication", False):
            self.use_password = self.config.as_bool("passwordauthentication")
        else:
            self.use_password = False


    # Begin interactive session
    def spawn_shell(self):
        interactive_shell(self.invoke_shell())



# https://github.com/paramiko/paramiko/blob/master/demos/interactive.py
# Launch interactive SSH session. Considers OS capabilities
def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)


def parse_options(*, sftp=False):

    # Add arguments
    parser = argparse.ArgumentParser()

    # Host.
    parser.add_argument(
        "host",
        help="Remote machine, formatted user@domain")
    if sftp:
        parser.add_argument(
            "destination",
            help="File destination; either remote host or local file"
        )
    parser.add_argument(
        "-F",
        "--config",
        help="Use config file"
    )
    parser.add_argument("-p", "--port",
        type=int,
        help="Port to connect to")
    parser.add_argument(
        "-6",
        "--IPv6",
        action="store_true",
        help="Use IPv6"
    )

    # Auth options
    parser.add_argument(
        "-i",
        "--identity-file",
        help="Path to key file"
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Username for authentication")
    pw_group = parser.add_mutually_exclusive_group()
    pw_group.add_argument(
        "--password",
        help="Add password (INSECURE)"
    )
    pw_group.add_argument(
        "--passfile",
        help="Path to file holding password"
    )
    return parser.parse_args()


# Parse user@host[:port] style string, returning (user, host, port)
def parse_host_string(args):

    host = args.host
    port = None
    user = None

    if args.user:
        user = args.user
    if args.port:
        port = args.port

    if "@" in host:
        user, host = host.split("@")
    if (":" in host) and not args.IPv6:
        port = host.split(":")
    
    return (user, host, port)


# Launch interactive SSH session on Unix client
def posix_shell(chan):

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = u(chan.recv(1024))
                    if len(x) == 0:
                        sys.stdout.write("\r\r*** EOF\r\n")
                        break
                    sys.stdout.write(x)
                    sys.stdout.flush()
                except socket.timeout:
                    pass

            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


def windows_shell(chan):
    pass

def read_passfile(file):
    with open(file, "r") as f:
        passw = f.read().strip()
    return passw


def main():

    client = Client.from_options()
    client.client_connect()
    client.spawn_shell()



if __name__ == '__main__':
    main()