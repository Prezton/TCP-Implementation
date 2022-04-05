import json
import sys
import argparse
import socket
import threading
# Stores connection information to handle different nodes
connection = dict()
BUFSIZE = 1024
lock = threading.Lock()

# Q1: do we need to do 3-way handshake to establish a connection?
# Q2: How do we handle multiple requests at the same time? e.g node2 and node4 asks for same file at the same time?
# Q3: what indeed does the simultaneous transfer mean?

class Tcpserver:
    def __init__(self):
        # {port: ACK number}, indicates a connection has been established
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
        connect_thread = threading.Thread(target=self.establish_connection, args=(ADDR, ))
        connect_thread.daemon = True
        connect_thread.start()
        msg_to_send = "ASKFILE" + "_" + str(self.port) + "_" + file_name
        # SEND FILE NAME FIRST
        if self.connection[ADDR]:
            print("CONNECTION SUCCESS")
            self.s.sendto(msg_to_send.encode(), ADDR)

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
        elif (msg.split("_")[0] == "ASKFILE"):
            self.handle_file(msg)

    def establish_connection(self, addr):
        dt = datetime.now()
        syn_num = datetime.timestamp(dt)
        self.s.sendto(syn_num.encode(), addr)
        while not self.connection[addr]:
            continue
        self.s.sendto((self.connection[addr] + 1).encode(), addr)

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