import paramiko
import ssh


# Creates SFTP client from SSH client
def sftp_from_client(client):
    sftp_client = paramiko.SFTPClient.from_transport(client.get_transport())


def main():

    args = ssh.parse_options()
    



if __name__ == '__main__':
    main()