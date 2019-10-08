#!/usr/bin/env python3
import argparse
import getpass
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



# Authenticate and connect to SSH server
def connect_client(host, port, user, password=None, keyfile=None):

    print("Initializing client...")
    ssh_client = paramiko.SSHClient()

    # Load host keys
    try:
        ssh_client.load_system_host_keys()
    except Exception as e:
        print("Error: failed to load host keys! %s" % e)

    # Auto-add server to trusted policy
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(
        host,
        port=port,
        username=user,
        password=password,
        key_filename=keyfile
    )

    return ssh_client


# https://github.com/paramiko/paramiko/blob/master/demos/interactive.py
# Launch interactive SSH session. Considers OS capabilities
def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)


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


    # Set Authentication
    user = args.user
    host = args.host
    port = args.port

    if args.password:
        password = args.password
    elif args.passfile:
        password = read_passfile(args.passfile)
    elif args.identity_file:
        password = None
    else:
        password = getpass.getpass()

    # Connect
    print(f"Connecting to {host}:{port} as {user}...")
    client = connect_client(host, port, user, password=password, keyfile=args.identity_file)

    # Create shell
    interactive_shell(client.invoke_shell())

    # End client connection
    client.close()



if __name__ == '__main__':

    # Add arguments
    parser = argparse.ArgumentParser()

    # Host
    parser.add_argument("host",
        help="Remote machine, formatted user@domain")
    parser.add_argument("-p", "--port",
        default=22,
        type=int,
        help="Port to connect to")

    # Auth options
    parser.add_argument(
        "-i",
        "--identity-file",
        default=None,
        help="Path to key file"
    )
    parser.add_argument(
        "-u",
        "--user",
        default="root",
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
    args = parser.parse_args()

    main()
