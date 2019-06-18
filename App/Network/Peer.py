from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Utils.SocketOp import SocketOp
import socket
import json

class Peer:
    def __init__(self):
        self.port = 65434
        self.boot_peer = ("192.168.50.10", self.port)

        self.reboot("")
        print("YOUR ADDRESS: {}".format(self.address))

        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind((self.address, self.port))

    def reboot(self, conn):
        print("CONNECTING TO BOOT PEER")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.boot_peer)
            self.address = s.getsockname()[0]
            s.send("R".encode("utf-8"))
            length = s.recv(100)
            length = int.from_bytes(length, byteorder="big")
            s.send("OK".encode("utf-8"))
            peers = SocketOp.recv(length, s)
            peers = json.loads(peers)
            print("PEERS: {}".format(peers))
            s.close()
        except Exception as e:
            print("BOOT PEER CONNECTION ERROR")
            print(e)
        if peers == "ONLY PEER":
            peers = []
        self.peers = peers
