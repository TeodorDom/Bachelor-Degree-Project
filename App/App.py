from sys import path as spath
from os import path
from time import sleep

spath.insert(0, path.abspath(path.join(path.dirname(__file__), "..")))

from App.Client.Mine import *
from App.Network.Peer import *
import threading
import jsonpickle

class App:
    def __init__(self):
        self.miner = Miner()
        self.peer = Peer()
        self.mine = True
        self.ps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pc.settimeout(8)
        self.ping_port = 65433
        self.ps.bind((self.peer.address, self.ping_port))
        self.start()

    def check_block(self, block):
        prev_block = self.miner.blockchain[-1]
        prev_block = self.miner.hash_block(prev_block)
        if block.header.prevblock != prev_block:
            return False
        if self.miner.get_timestamp() < block.header.timestamp:
            return False
        if len(block.transactions) != block.no_tx:
            return False

        for tx in block.transactions:
            if self.transaction(tx) == False:
                return False

        tree = Merkle(block.transactions)
        if tree.get_root() != block.header.merkle:
            return False
        if self.miner.check(block) == False:
            return False
        return True

    def block(self, conn):
        # checks received block
        conn.sendall("OK".encode("utf-8"))
        size = conn.recv(100)
        size = int.from_bytes(size, byteorder="big")
        conn.sendall("OK".encode("utf-8"))
        block = conn.recv(size)
        block = jsonpickle.decode(block.decode("utf-8"))
        b = self.check_block(block)
        if b == True:
            self.send_block(block)
        conn.sendall([int(b)])

    def counter_block(self, conn):
        pass

    def inactive(self, conn):
        # sends inactive notification to the BS
        pass

    def transaction(self, conn):
        # checks transaction
        return True

    def server(self):
        options = {
            "B": self.block,
            "b": self.counter_block,
            "T": self.transaction,
            "r": self.peer.reboot
        }
        while True:
            print("LISTENING")
            self.peer.ss.listen(10)
            conn, addr = self.peer.ss.accept()
            option = conn.recv(1).decode("utf-8")
            conn.sendall("OK".encode("utf-8"))
            options[option](conn)
            conn.close()

    def client(self):
        # used to send requests and payloads
        pass

    def pings(self):
        while True:
            self.ps.listen(50)
            conn, addr = self.ps.accept()
            option = conn.recv(1).decode("utf-8")
            conn.sendall("OK".encode("utf-8"))
            conn.close()

    def pingc(self):
        while True:
            for p in self.peer.peers:
                try:
                    print("PINGING {}".format(p))
                    self.pc.connect((p, self.ping_port))
                    self.pc.sendall("p".encode("utf-8"))
                    response = self.pc.recv(2)
                    print("{} ACTIVE!".format(p))
                except:
                    print("{} INACTIVE!".format(p))
                sleep(5)

    def ping(self):
        pserver = threading.Thread(target = self.pings)
        pclient = threading.Thread(target = self.pingc)
        pserver.start()
        pclient.start()

    def start(self):
        # self.server()
        # self.client()
        self.ping()

if __name__ == "__main__":
    app = App()
    while True:
        pass
