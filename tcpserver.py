import json
import sys
import argparse
import socket
import threading
from datetime import datetime
import random

# Stores connection information to handle different nodes
connection = dict()
BUFSIZE = 2048
lock = threading.Lock()
CHUNKSIZE = 1024
HEADER_LENGTH = 32
ESTABLISH_FLAG = 3
SYNC_FLAG = 4
ACK_FLAG = 5
FIN_FLAG = 6



class Connection:
    def __init__(self):
        self.sync_num = -1
        self.ack_num = -1
        self.filename = None
        self.port = -1
        self.fileobject = None
        self.timestamp = 0
        self.prev_msg = None

# Q1: How do I have a fixed length header?
# Q2: does socket.recvfrom(BUFSIZE) return bytes sent by different source nodes?

class Tcpserver:
    def __init__(self):
        # {port: Connection}, indicates a connection has been established
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

    def client_handle(self):
        while True:
            # print("LISTENING ON ", self.port)
            msg_addr = self.s.recvfrom(BUFSIZE)
            self.message_handle(msg_addr)

            # message_handle_thread = threading.Thread(target=self.message_handle, args=(msg_addr,))
            # message_handle_thread.daemon = True
            # message_handle_thread.start()

    def message_handle(self, msg_addr):
        # ESTABLISH == 3, SYNC == 4, ACK == 5
        msg = msg_addr[0]
        client_addr = msg_addr[1]
        header = msg[:32].decode()
        # print("RECEIVED MSG'S HEADER IS: ", header)
        flag = int(header[0])
        # As a server, receives ACK and continues to send files
        if (flag == 5):
            self.send_file(msg, client_addr)
        # As a client, receives syn message and save file locally
        elif (flag == 4):
            self.handle_file(header, msg, client_addr)
        # As a server, passively received establish signal with the file name
        elif (flag == 3):
            self.handle_establish_req(msg, client_addr)
            self.send_file(None, client_addr)
        elif (flag == 6):
            self.end_transmission(client_addr)

    def handle_establish_req(self, msg, client_addr):
        filename = msg[32:].decode()
        node_key = client_addr[1]
        # print("NODE KEY IS: ", node_key, "TYPE IS: ", type(node_key))
        # print("SERVER RECEIVED FILE NAME IS: ", filename)
        self.connection[node_key] = Connection()
        self.connection[node_key].filename = filename

    def send_file(self, msg, client_addr):
        # print("SEND FILE")
        node_key = client_addr[1]
        conn = self.connection[node_key]
        filename = conn.filename
        if not conn.fileobject:
            f = open(filename, "rb")
            conn.fileobject = f
        else:
            f = conn.fileobject
        if msg:
            ack_num = int((msg[:32].decode())[1:])
            f.seek(ack_num - 1)
            # print("RECEIVED ACK: ", ack_num)
            # print("set offset")
        bytes = f.read(CHUNKSIZE)

        if not bytes:
            header = str(FIN_FLAG)
            header += ("0" * 31)
            self.s.sendto(header.encode(), client_addr)
            return

        conn.sync_num = f.tell()
        sync_num = str(conn.sync_num)

        header = str(SYNC_FLAG)
        tmp = 32 - len(header) - len(sync_num)
        header += ("0" * tmp)
        header += sync_num
        # print("SEND_FILE(): HEADER IS: ", header)
        msg_to_send = header.encode() + bytes
        self.s.sendto(msg_to_send, client_addr)


    def resend_ack(self):
        resend_thread = threading.Timer(0.05, self.resend_ack)
        resend_thread.daemon = True
        resend_thread.start()
        for node_key in self.connection:
            conn = self.connection[node_key]
            ADDR = ("localhost", node_key)
            if conn.timestamp != 0 and datetime.timestamp(datetime.now()) - conn.timestamp > 0.1:
                # print("RESEND ack: ", int(conn.prev_msg.decode()[1:]))
                self.s.sendto(conn.prev_msg, ADDR)

# CLIENT METHODS BELOW, SERVER METHODS ABOVE

    def establish_connection(self, addr, file_name):
        sync_num = random.randint(100, 200)
        header = str(ESTABLISH_FLAG)
        header += ("0" * 31)
        req_msg = header + file_name
        node_key = addr[1]
        self.connection[node_key] = Connection()
        self.connection[node_key].filename = file_name
        # self.latest_syn_num[addr[1]] = sync_num
        self.s.sendto(req_msg.encode(), addr)
        # print("ESTABLISH REQ SENT, NODE KEY IN CLIENT IS: ", node_key, "TYPE IS: ", type(node_key))


    def request_file(self, file_name):
        target = None
        for peer in self.peer_info:
            if file_name in peer["content_info"]:
                target = peer
                # print("FILE EXIST ON: ", peer["port"])
        if not target:
            print("DOES NOT EXIST IN PEER NODES")
            return
        target_port = int(target["port"])
        target_name = target["hostname"]
        target_addr = socket.gethostbyname(target_name)
        ADDR = (target_addr, target_port)

        node_key = target_port

        # As a client, initiate a connection and SEND FILE NAME FIRST
        if node_key not in self.connection:
            self.establish_connection(ADDR, file_name)
        self.resend_ack()

    def handle_file(self, header, msg, client_addr):
        msg = msg[32:]
        sync_num = int(header[1:])
        ack_num = str(sync_num + 1)
        # print("received sync_num: ", sync_num)
        node_key = client_addr[1]
        conn = self.connection[node_key]
        filename = conn.filename
        if not conn.fileobject:
            f = open(filename, "wb")
            conn.fileobject = f
        else:
            f = conn.fileobject
        f.write(msg)

        header = str(ACK_FLAG)
        tmp = 32 - len(header) - len(ack_num)
        header = header + "0" * tmp + ack_num
        # print("HANDLE_FILE() CLIENT ACK NUM IS:", header)
        self.s.sendto(header.encode(), client_addr)
        conn.prev_msg = header.encode()
        conn.timestamp = datetime.timestamp(datetime.now())
        # print("send ack", ack_num)


    def end_transmission(self, client_addr):
        node_key = client_addr[1]
        conn = self.connection[node_key]
        f = conn.fileobject
        f.close()
        del self.connection[node_key]



if __name__ == "__main__":
    path = sys.argv[1]
    server = Tcpserver()
    server.set_config(path)
    # server.print_args()
    server.create_socket()
    # print("SOCKET: ", (server.s != None))

    client_thread = threading.Thread(target=server.client_handle)
    client_thread.daemon = True
    client_thread.start()

    while True:
        file_name = input()
        server.request_file(file_name)