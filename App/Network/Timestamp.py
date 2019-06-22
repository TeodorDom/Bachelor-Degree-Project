from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Utils.RSA import MP_RSA
from App.Utils.SocketOp import SocketOp
from time import time
import socket
import threading
import jsonpickle

class Timestamp():
    def __init__(self):
        self.rsa = MP_RSA(512)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind(("192.168.50.8", 65432))
        t = threading.Thread(target = self.start)
        t.start()

    def start(self):
        print("TIMESTAMP SERVER STARTED")
        while True:
            try:
                self.ss.listen(50)
                conn, addr = self.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                data = self.rsa.sign(str(time()))
                data = jsonpickle.encode(data).encode("utf-8")
                length = len(data)
                SocketOp.send(str(length).encode("utf-8"), conn)
                response = conn.recv(2)
                SocketOp.send(data, conn)
                conn.close()
            except Exception as e:
                print("COULD NOT SEND TIMESTAMP")
                print(e)

if __name__ == "__main__":
    ts = Timestamp()
