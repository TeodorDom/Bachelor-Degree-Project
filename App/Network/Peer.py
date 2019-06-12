import socket
import json

class Peer:
    def __init__(self):
        self.port = 65434
        self.boot_peer = ("192.168.50.10", self.port)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.settimeout(8)
        self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cs.settimeout(8)
        self.reboot(self.cs)
        print("YOUR ADDRESS: {}".format(self.address))

    def reboot(self, conn):
        print("CONNECTING TO BOOT PEER")
        try:
            self.cs.connect(self.boot_peer)
            self.address = self.cs.getsockname()[0]
            self.cs.send("R".encode("utf-8"))
            length = self.cs.recv(100)
            length = int.from_bytes(length, byteorder="big")
            self.cs.send("OK".encode("utf-8"))
            peers = self.cs.recv(length).decode("utf-8")
            peers = json.loads(peers)
            print("PEERS: {}".format(peers))
        except:
            print("CONNECTION ERROR")
        if peers == "ONLY PEER":
            peers = []
        self.peers = peers


if __name__ == "__main__":
    p = Peer()
