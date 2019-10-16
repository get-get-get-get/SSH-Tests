#!/usr/bin/env python3
import getpass
import os
import paramiko
import pathlib
import ssh


# TODO: rewrite to be understandable and not garbage


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
    if (":" in host) and not args.IPv6:
        host, port = host.split(":")
        port = int(port)

    return (user, host, port, resource)


def main():

    client = ssh.Client.from_options(sftp=True)
    client.client_connect()
    sftp = client.open_sftp()
    
    if client.scp_method == "get":
        if os.path.isdir(client.local_resource):
            name = pathlib.PurePath(client.resource).name
            client.local_resource = os.path.join(client.local_resource, name)
        print(f"Copying {client.resource} to {client.local_resource}")
        sftp.get(client.resource, client.local_resource)
    else:
        print(f"Copying {client.local_resource} to {client.resource}")
        sftp.put(client.local_resource, client.resource)
    
    # TODO: put in better location or something
    try:
        sftp.close()
        client.close()
    except:
        pass


if __name__ == '__main__':
    main()
