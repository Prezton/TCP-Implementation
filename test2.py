import pickle
import json
import socket
import sys
from time import sleep

f = open("tcpserver.py", "rb")
bytes = f.read(1024)
class Header:
    def __init__(self):
        self.ack = 90000999999999999
        self.sync = 9000000009870000
        self.flag = 1024000000000000

string ="90000999999999999" + "90000000098700000" + "1024000000000000"
print(len(string.encode()), type(string.encode()))

bytes = pickle.dumps(Header())
print(len(bytes), type(bytes))


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

localip = "localhost"

try:
    s.bind((localip, 18742))
except socket.error as e:
    sys.exit(-1)

while True:
    sleep(5)
    b = s.recvfrom(100000)
    print(b)
