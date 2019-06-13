from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.dirname(__file__), "..")))

from App.Client.Mine import *
from App.Network.Peer import *
from time import sleep
import threading
import jsonpickle
import random

class App:
    def __init__(self):
        self.lock = threading.Lock()
        self.miner = Miner()
        self.peer = Peer()

        self.ps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ps.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

    def send_block(self, block):
        for p in self.peer.peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((p, self.peer.port))

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

    def inactive(self, addr):
        # sends inactive notification to the BS
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.peer.boot_peer)
        s.sendall("I".encode("utf-8"))
        s.sendall(addr.encode("utf-8"))

    def transaction(self, conn):
        # checks transaction
        return True

    def server(self):
        options = {
            "B": self.block,
            "T": self.transaction,
            "r": self.peer.reboot
        }
        print("SERVER STARTED")
        while True:
            self.peer.ss.listen(25)
            try:
                conn, addr = self.peer.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                # USE LOCK
                # self.lock.acquire()
                option = conn.recv(1).decode("utf-8")
                conn.sendall("OK".encode("utf-8"))
                options[option](conn)
                # conn.close()
            except Exception as e:
                print("CONNECTION ERROR")
                print(e)
            # RELEASE LOCK
            # self.lock.release()

    def client(self):
        # used to mine and send requests and payloads
        # acquire lock before mining ONE iteration; check for changes after getting the lock
        while True:
            input_value = random.randint(1, 100)
            output_value = str(random.randint(1, input_value))
            input_value = str(input_value)

            transactions = [Transaction([TXInput("a",input_value,"a")], [TXOutput(output_value,"b")])]
            transactions += [Transaction([TXInput("b",input_value,"b")], [TXOutput(output_value,"c")])]
            transactions += [Transaction([TXInput("c",input_value,"c")], [TXOutput(output_value,"d")])]
            transactions += [Transaction([TXInput("d", input_value, "d")], [TXOutput(output_value, "e")])]
            transactions += [Transaction([TXInput("e", input_value, "e")], [TXOutput(output_value, "f")])]

            tree = Merkle(transactions)
            candidate_header = BlockHeader(self.miner.hash_block(self.miner.blockchain[-1]),
                                           tree.get_root(), self.miner.get_timestamp(), 0)
            candidate = Block(candidate_header, transactions)

            while self.miner.check(candidate) == False:
                candidate.header.nonce += 1

            print("FOUND BLOCK {}".format(candidate))
            self.miner.save_block(candidate)
        pass

    def pings(self):
        while True:
            self.ps.listen(50)
            conn, addr = self.ps.accept()
            print("PING FROM {}".format(addr))
            option = conn.recv(1).decode("utf-8")
            conn.sendall("OK".encode("utf-8"))
            conn.close()

    def pingc(self):
        while True:
            # self.lock.acquire()
            i = 0
            count = 0
            while i < len(self.peer.peers):
                pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                pc.settimeout(8)
                try:
                    print("PINGING {}".format(self.peer.peers[i]))
                    pc.connect((self.peer.peers[i], self.ping_port))
                    pc.sendall("p".encode("utf-8"))
                    response = pc.recv(2)
                    print("{} ACTIVE!".format(self.peer.peers[i]))
                    i += 1
                    count = 0
                except:
                    print("{} INACTIVE!".format(self.peer.peers[i]))
                    count += 1
                    if count == 2:
                        self.inactive(self.peer.peers[i])
                        count = 0
                        i += 1
                pc.close()
                sleep(5)
            # self.lock.release()
            sleep(10)

    def ping(self):
        pserver = threading.Thread(target = self.pings)
        pclient = threading.Thread(target = self.pingc)
        pserver.start()
        pclient.start()

    def start(self):
        t_server = threading.Thread(target = self.server)
        t_server.start()
        # self.client()
        self.ping()

if __name__ == "__main__":
    app = App()
    while True:
        pass
