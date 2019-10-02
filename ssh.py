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

import forward



# Authenticate and connect to SSH server
def connect_client(host, port, user, password=None, keyfile=None):

    print("Initializing client...")
    ssh_client = paramiko.SSHClient()

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


# Read password from file
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
        password = getpass.getpass

    try:
        # Connect
        client = connect_client(host, port, user, password=password, keyfile=args.identity_file)
    except Exception as e:
        print(f"Connection Error: {e}")
        exit()
    
    try: 
        
        if not args.non_interactive:
            # Create shell
            try:
                interactive_shell(client.invoke_shell())
            except KeyboardInterrupt:
                print(f"Ending interactive session with {host}")

        # Local port forwarding
        if args.local_forward:
            fwd = args.local_forward.split(":")
            if len(fwd) != 3:
                print(f"Local Forward Error: invalid args -- {args.local_forward}")
                client.close()
                exit()
            
            # Important variables
            lport = fwd[0]
            rhost = fwd[1]
            rport = fwd[2]

            forward.forward_tunnel(lport, rhost, rport, client)

    # Catch uncaught exceptions and guarantee connection closes
    finally:
        # End client connection
        print(f"Closed connection to {host}")
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

    # Shell options
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive shell"
    )

    # Forwarding options
    parser.add_argument(
        "-L",
        "--local-forward",
        help="Port forward from local port. Formate {lport}:{rhost}:{rport}"
    )

    args = parser.parse_args()

    main()
