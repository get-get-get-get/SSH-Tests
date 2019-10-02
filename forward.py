import sys
import paramiko
import socket

# Compatibility
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer



class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class SubHandler(Handler):
    
    def __init__(self, remote_host, remote_port, transport):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport


# Do a local port forward
def forward_tunnel(lport, rhost, rport, transport):

    sub_handler = SubHandler(rhost, rport, transport)

    # Run server
    ForwardServer(("", lport), sub_handler).serve_forever()