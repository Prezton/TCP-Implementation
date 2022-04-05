import json
import sys
import argparse
import socket
import threading
# Stores connection information to handle different nodes
connection = dict()
BUFSIZE = 1024
lock = threading.Lock()

class Tcpserver:
    def __init__(self):
        # {port: ACK number}
        self.connection = dict()

    def set_config(self, path):
        with open(path, "r") as f:
            config = json.loads(f.read())
        self.hostname = config["hostname"]
        self.port = int(config["port"])
        self.peer_count = int(config["peers"])
        self.content = config["content_info"]
        self.peer_info = config["peer_info"]

    def print_args(self):
        print(self.hostname, self.port, self.peer_info, self.content, self.peer_count, self.connection)

    def create_socket(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # localip = socket.gethostbyname(socket.gethostname())
        localip = "127.0.0.1"

        try:
            self.s.bind((localip, self.port))
        except socket.error as e:
            sys.exit(-1)

    def request_file(self, file_name):
        target = None
        for peer in self.peer_info:
            if file_name in peer["content_info"]:
                target = peer
        if not target:
            print("DOES NOT EXIST IN PEER NODES")
            return
        target_port = int(target["port"])
        target_name = target["hostname"]
        target_addr = socket.gethostbyname(target_name)
        ADDR = (target_addr, target_port)
        file_name = file_name.encode()
        self.s.sendto(file_name, ADDR)

    def send_file(self):
        pass

    def send_ack(self):
        pass

    def handle_ack(self, msg):
        pass

    def handle_file(self, msg):
        pass

    def client_handle(self):
        while True:
            # print("LISTENING ON ", self_backendport)
            msg_addr = self.s.recvfrom(BUFSIZE)
            message_handle_thread = threading.Thread(target=self.message_handle, args=(msg_addr, ))
            message_handle_thread.daemon = True
            message_handle_thread.start()

    def message_handle(self, msg_addr):
        msg = msg_addr[0]
        client_addr = msg_addr[1]
        if (msg.split("_")[0] == "ACK"):
            # print("RECEIVED FROM LOCAL HOST")
            self.handle_ack(msg)
        else:
            self.handle_file(msg)



if __name__ == "__main__":
    path = sys.argv[1]
    server = Tcpserver()
    server.set_config(path)
    server.print_args()
    server.create_socket()

    client_thread = threading.Thread(target=server.client_handle)
    client_thread.daemon = True
    client_thread.start()

    while True:
        file_name = input()
        server.request_file(file_name)