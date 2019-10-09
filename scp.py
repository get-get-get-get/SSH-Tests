import os
import paramiko
import ssh


# Creates SFTP client from SSH client
def sftp_from_client(client):
    sftp_client = paramiko.SFTPClient.from_transport(client.get_transport())


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



def main():

    args = ssh.parse_options(scp=True)
    # This doesn't really work because args.destination might actually have hoststring
    user, host, port = ssh.parse_host_string(args)






if __name__ == '__main__':
    main()