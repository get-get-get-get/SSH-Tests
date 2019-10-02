import paramiko
import select
import sys
import socket

# Compatibility
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer



class ForwardServer(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(SocketServer.BaseRequestHandler):

    def __init__(self, ssh_chan, verbose=False):
        chan = ssh_chan
        verbose = verbose
    

    def handle(self):
        chan = self.chan

        while True:
            r, w, x = select.select([self.request, chan], [], [])

            if self.request in r:
                data  = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
        
        # Close connection
        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        if self.verbose:
            print(f"Tunnel closed from {peername}")


class SubHandler(Handler):
    
    def __init__(self, remote_host, remote_port, transport):
        chain_host = remote_host
        chain_port = remote_port
        ssh_transport = transport


# Do a local port forward
def forward_tunnel(lport, rhost, rport, client=None, transport=None, chan=None):

    if client and not chan: 
        chan = client.invoke_shell()
    if client and not transport:
        transport = client.get_transport()      
    
    handler = Handler(chan)
    sub_handler = SubHandler(rhost, rport, transport)

    print(f"listening on {lport}, forwarding to {rhost}:{rport}")
    print(f":{lport} -> {rhost}:{rport}")
    
    # Run server
    ForwardServer(("", lport), sub_handler).serve_forever()