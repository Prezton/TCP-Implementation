import json
import sys
import argparse
import socket
import threading
import datetime
import random

# Stores connection information to handle different nodes
connection = dict()
BUFSIZE = 10240
lock = threading.Lock()

class Node:
    def __init__(self):
        self.seq = -1
        self.ack = -1

# Q1: do we need to do 3-way handshake to establish a connection?
# Q2: How do we handle multiple requests at the same time? e.g node2 and node4 asks for same file at the same time?
# Q3: what indeed does the simultaneous transfer mean?

class Tcpserver:
    def __init__(self):
        # {port: ACK number}, indicates a connection has been established
        self.connection = dict()
        self.latest_syn_num = dict()

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

        node_key = (target_addr, target_port, file_name)

        # As a client, initiate a connection and SEND FILE NAME FIRST
        if node_key not in self.connection:
            self.establish_connection(node_key)





    def send_file(self):
        pass

    def send_ack(self, msg, addr):
        print("SEND ACK")
        flag = msg.split("_")[0]
        if flag == "SYNC":
            sync_num = int(msg.split("_")[1])
            ack_num = sync_num + 1
            ack_msg = "ACK" + "_" + str(ack_num)
            self.s.sendto(ack_msg.encode(), addr)
            return True
        else:
            print("NOT ESTABLISH SIGNAL")

    def handle_ack(self, msg, addr):
        print("HANDLE ACK")
        filename =
        node_key = msg.split("_")
        lock.acquire()
        if addr[1] not in self.connection:
            if addr[1] in self.latest_syn_num:
                if int(msg.split("_")[1]) == self.latest_syn_num[addr[1]] + 1:
                    self.connection[addr[1]] = addr
                    lock.release()
                    print("CONNECTION ESTABLISHED")
                    return True
                else:
                    print("ACK AND SYNC DOES NOT MATCH")
            else:
                print("SYNC NUM NOT RECORDED, THIS SHOULD NOT HAPPEN")
        else:
            print("CONNECTION ALREADY ESTABLISHED")
        lock.release()

    def handle_file(self, msg):
        pass

    def send_sync(self, addr):
        print("SEND SYNC")
        sync_num = random.randint(201, 301)
        sync_msg = "SYNC" + "_" + str(sync_num)

        # addr[1] is a integer!
        # print("TYPE IS: ", type(addr[1]))

        self.latest_syn_num[addr[1]] = sync_num
        self.s.sendto(sync_msg.encode(), addr)

    def handle_sync(self, msg, addr):
        print("HANDLE SYNC")
        # self.send_ack(msg, addr)
        pass

    def client_handle(self):
        while True:
            print("LISTENING ON ", self.port)
            msg_addr = self.s.recvfrom(BUFSIZE)

            message_handle_thread = threading.Thread(target=self.message_handle, args=(msg_addr,))
            message_handle_thread.daemon = True
            message_handle_thread.start()

    def message_handle(self, msg_addr):
        msg = msg_addr[0]
        client_addr = msg_addr[1]
        msg = msg.decode()
        print("MESSAGE IS: ", msg)
        flag = msg.split("_")[0]
        # As a server, receives ACK and continues to send files
        if (flag == "ACK"):
            self.handle_ack(msg, client_addr)
        # As a client, receives syn message and save file locally
        elif (flag == "SYNC"):
            self.handle_sync(msg, client_addr)
        # As a server, passively received establish signal with the file name
        elif (flag == "ESTABLISH"):
            self.handle_file_req(msg, client_addr)
            # Send the first chunk
            self.send_file(msg, client_addr)

    def handle_file_req(self, msg, client_addr):
        filename = msg.split("_")[0]
        node_key = (client_addr[0], client_addr[1], filename)
        print("NODE KEY IS: ", node_key)
        self.connection[node_key] = Node()
        print("SERVER RECEIVED FILE NAME IS: ", filename)


    def establish_connection(self, node_key):
        sync_num = random.randint(100, 200)
        sync_msg = "ESTABLISH" + "_" + node_key[2]
        # self.latest_syn_num[addr[1]] = sync_num
        addr = (node_key[0], node_key[1])
        self.s.sendto(sync_msg.encode(), addr)
        print("ESTABLISH REQ SENT, NODE KEY IN CLIENT IS: ", node_key)
        self.connection[node_key] = Node()


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

    while True:pro
        file_name = input()
        server.request_file(file_name)