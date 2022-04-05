import json
import sys
import argparse
import socket
import threading
import datetime
import random

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
        localip = "localhost"

        try:
            self.s.bind((localip, self.port))
        except socket.error as e:
            sys.exit(-1)

    def request_file(self, file_name):
        target = None
        for peer in self.peer_info:
            if file_name in peer["content_info"]:
                target = peer
                print("FILE EXIST ON: ", peer["port"])
        if not target:
            print("DOES NOT EXIST IN PEER NODES")
            return
        target_port = int(target["port"])
        target_name = target["hostname"]
        target_addr = socket.gethostbyname(target_name)
        ADDR = (target_addr, target_port)

        # As a client, initiate a connection
        if ADDR[1] not in self.connection:
            self.establish_connection(ADDR)
        msg_to_send = "ASKFILE" + "_" + str(self.port) + "_" + file_name
        # SEND FILE NAME FIRST
        if ADDR[1] in self.connection:
            print("CONNECTION SUCCESS")
            self.s.sendto(msg_to_send.encode(), ADDR)

    def send_file(self):
        pass

    def send_ack(self, msg, addr):
        print("SEND ACK")
        flag = msg.split("_")[0]
        if flag == "ESTABLISH" or "SYNC":
            sync_num = int(msg.split("_")[1])
            ack_num = sync_num + 1
            ack_msg = "ACK" + "_" + str(ack_num)
            self.s.sendto(ack_msg.encode(), addr)
            return True
        else:
            print("NOT ESTABLISH SIGNAL")

    def handle_ack(self, msg, addr):
        print("HANDLE ACK")
        lock.acquire()
        if addr[1] not in self.connection:
            self.connection[addr[1]] = addr
            lock.release()
            print("CONNECTION ESTABLISHED")
            return True
        lock.release()

    def handle_file(self, msg):
        pass

    def send_sync(self, addr):
        print("SEND SYNC")
        sync_num = random.randint(201, 301)
        sync_msg = "SYNC" + "_" + str(sync_num)
        self.s.sendto(sync_msg.encode(), addr)

    def handle_sync(self, msg, addr):
        print("HANDLE SYNC")
        self.send_ack(msg, addr)

    def client_handle(self):
        while True:
            print("LISTENING ON ", self.port)
            msg_addr = self.s.recvfrom(BUFSIZE)
            print("GOT MSG!!!")

            message_handle_thread = threading.Thread(target=self.message_handle, args=(msg_addr,))
            message_handle_thread.daemon = True
            message_handle_thread.start()

    def message_handle(self, msg_addr):
        msg = msg_addr[0]
        client_addr = msg_addr[1]
        msg = msg.decode()
        print("msg is: ", msg)
        if (msg.split("_")[0] == "ACK"):
            self.handle_ack(msg, client_addr)
        # As a client, receives ack and syn message
        elif (msg.split("_")[0] == "SYNC"):
            self.handle_sync(msg, client_addr)
        # As a server, passively received establish sync signal
        elif (msg.split("_")[0] == "ESTABLISH"):
            self.send_ack(msg, client_addr)
            self.send_sync(client_addr)

    def establish_connection(self, addr):
        sync_num = random.randint(100, 200)
        sync_msg = "ESTABLISH" + "_" + str(sync_num)
        self.s.sendto(sync_msg.encode(), addr)
        print("ESTABLISH REQ SENT", addr)


if __name__ == "__main__":
    path = sys.argv[1]
    server = Tcpserver()
    server.set_config(path)
    # server.print_args()
    server.create_socket()
    print("SOCKET: ", (server.s != None))

    client_thread = threading.Thread(target=server.client_handle)
    client_thread.daemon = True
    client_thread.start()

    while True:
        file_name = input()
        server.request_file(file_name)