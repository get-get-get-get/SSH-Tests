import getpass
import os
import paramiko
import ssh


# Creates SFTP client from SSH client
def sftp_from_client(client):
    return paramiko.SFTPClient.from_transport(client.get_transport())


# Identifies which is the Remote machine and which is local. Return (remote, local)
def find_remote(x, y):

    if (":" in x) and not (":" in y):
        return (x, y)
    elif (":" in y) and not (":" in x):
        return (y, x)

    if (os.path.exists(x)) and not (os.path.exists(y)):
        return (x, y)
    elif (os.path.exists(y)) and not (os.path.exists(x)):
        return (y, x)

    # TODO: better


# Parse scp host syntax
# Returns (user, host, port, resource)
def parse_scp_host(args):

    remote, __ = find_remote(args.host, args.destination)

    host, resource = remote.rsplit(":", maxsplit=1)
    user = None
    port = None

    if "@" in host:
        user, host = host.split("@")
    if host.contains(":") and not args.IPv6:
        host, port = host.split(":")
        port = int(port)

    if user is None and args.user is None:
        user = "root"
    if port is None:
        port = args.port

    return (user, host, port, resource)


def main():

    # Parse options
    args = ssh.parse_options(scp=True)
    user, host, port, resource = parse_scp_host(args)

    if args.password:
        password = args.password
    elif args.passfile:
        password = ssh.read_passfile(args.passfile)
    elif args.identity_file:
        password = None
    else:
        password = getpass.getpass()

    # Connect
    print(f"Authenticating to {host}:{port} as {user}...")
    ssh_client = ssh.connect_client(host, port, user, password=password, keyfile=args.identity_file)
    sftp_client = sftp_from_client(ssh_client)
    
    # Determine method
    remote, local = find_remote(args.host, args.destination)
    if remote == args.host:
        do_get = True
    else:
        do_get = False
    
    if do_get:
        print(f"Copying {resource} to {local}")
        sftp_client.get(resource, local)
    else:
        print(f"Copying {local} to {resource}")
        sftp_client.put(local, resource)



if __name__ == '__main__':
    main()
