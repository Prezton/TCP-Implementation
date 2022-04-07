import pickle
import json
import socket
import sys

f = open("tcpserver.py", "rb")
bytes = f.read(1024)
class Header:
    def __init__(self):
        self.ack = 90000999999999999
        self.sync = 9000000009870000
        self.flag = 1024000000000000

string ="00001"
string2 = "9000099999999999990000000098700001024000000000000"

print(len(string.encode()), type(string.encode()))

bytes = pickle.dumps(Header())
# print(len(bytes), type(bytes))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

localip = "localhost"

try:
    s.bind((localip, 18741))
except socket.error as e:
    sys.exit(-1)

s.sendto(string.encode(), (localip, 18742))

f = open("Carnegie_Mellon_University.jpg", "rb")

while True:
    bytes = f.read(1024)
    print(f.tell())
    f.seek(2048)
    if not bytes:
        print("READ DONE")
        break

