import socket
import json

class Peer:
    def __init__(self):
        self.port = 65434
        self.boot_peer = ("192.168.50.10", self.port)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peers = self.get_peers()

    def get_peers(self):
        # requires interation with the boot peer
        print("CONNECTING TO BOOT PEER")
        # try:
        self.cs.connect(self.boot_peer)
        length = self.cs.recv(100)
        length = int.from_bytes(length, byteorder="big")
        print(length)
        self.cs.send("OK".encode("utf-8"))
        peers = self.cs.recv(length).decode("utf-8")
        print(peers)
        peers = json.loads(peers)
        print(peers)
        # except:
        #     print("CONNECTION ERROR")
        #     peers = []
        return peers

if __name__ == "__main__":
    p = Peer()
