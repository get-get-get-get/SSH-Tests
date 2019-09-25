#!/usr/bin/env python3
import argparse
import getpass
import paramiko



def connect_client(host, port, user, password=None, keyfile=None):

    print("Initializing client...")
    ssh_client = paramiko.SSHClient()

    # Auto-add server to trusted policy
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(
        host,
        port=port,
        username=user,
        password=password
    )
    
    return ssh_client


def read_passfile(file):
    with open(file, "r") as f:
        passw = f.read().strip()
    return passw


def main():

    if args.identity_file:
        print("Haven't implemented identity files yes lmao")
        exit()
    
    # Authentication
    user = args.user

    if args.password:
        password = args.password
    elif args.passfile:
        password = read_passfile(args.passfile)
    else:
        password = getpass.getpass

    client = connect_client(args.host, args.port, args.user, password=password)

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
        help="Path to key file"
    )
    parser.add_argument(
        "-u",
        "--user",
        Required=True,
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
