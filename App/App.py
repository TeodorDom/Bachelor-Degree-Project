from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.dirname(__file__), "..")))

import jsonpickle
import bitstring as bs
from App.Client.Mine import *
from App.Network.Peer import *
from time import sleep
import threading
import random

class App:
    def __init__(self):
        self.lock = threading.Semaphore(2)
        self.miner = Miner()
        self.peer = Peer()
        self.changed = False

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
            if self.verify_transaction(tx) == False:
                return False

        tree = Merkle(block.transactions)
        if tree.get_root() != block.header.merkle:
            return False
        if self.miner.check(block) == False:
            return False
        return True

    def send_block(self, block):
        denied = 0
        no_denies = len(self.peer.peers) // 3
        for p in self.peer.peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((p, self.peer.port))
                s.sendall("B".encode("utf-8"))
                response = s.recv(2)
                data = jsonpickle.encode(block).encode("utf-8")
                length = len(data)
                s.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
                response = s.recv(2)
                s.sendall(data)
                response = s.recv(1)
                response = int.from_bytes(response, byteorder="big")
            except Exception as e:
                print("CONNECTION WITH {} FAILED, {}".format(p,e))
            if response == 0:
                denied += 1
            if denied >= no_denies:
                return False
        return True

    def verify_transaction(self, tx):
        return True

    def verify_block(self, conn):
        # checks received block
        print("CHECKING BLOCK")
        # conn.sendall("OK".encode("utf-8"))
        size = conn.recv(100)
        size = bs.BitArray(bytes = size).uint
        conn.sendall("OK".encode("utf-8"))
        block = conn.recv(size)
        block = jsonpickle.decode(block.decode("utf-8"))
        b = self.check_block(block)
        conn.sendall(bytes([int(b)]))

        peer_opinion = False
        if b == True:
            peer_opinion = self.send_block(block)
        self.changed = peer_opinion
        print("Change Blockchain? {}".format(peer_opinion))
        if peer_opinion == True:
            self.miner.save_block(block)
        print("BLOCKCHAIN: {}".format(self.miner.blockchain))

    def inactive(self, addr):
        # sends inactive notification to the BS
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.peer.boot_peer)
        s.sendall("I".encode("utf-8"))
        s.sendall(addr.encode("utf-8"))

    def get_transaction(self, conn):
        # checks transaction
        return True

    def send_blockchain(self, conn):
        data = jsonpickle.encode(self.miner.blockchain).encode("utf-8")
        length = len(data)
        conn.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
        response = conn.recv(2)
        conn.sendall(data)

    def send_ledger(self, conn):
        data = jsonpickle.encode(self.miner.ledger).encode("utf-8")
        length = len(data)
        conn.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
        response = conn.recv(2)
        conn.sendall(data)

    def server(self):
        options = {
            "B": self.verify_block,
            "T": self.get_transaction,
            "r": self.peer.reboot,
            "b": self.send_blockchain,
            "l": self.send_ledger
        }
        print("SERVER STARTED")
        while True:
            self.peer.ss.listen(25)
            try:
                conn, addr = self.peer.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                self.lock.acquire()

                option = conn.recv(1).decode("utf-8")
                conn.sendall("OK".encode("utf-8"))
                options[option](conn)
                conn.close()
            except Exception as e:
                print("CONNECTION ERROR -> {}".format(option))
                print("REASON {}".format(e))
            self.lock.release()

    def get_blockchain(self):
        blockchain = []
        for peer in self.peer.peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            temp = []
            try:
                s.connect((peer, self.peer.port))
                s.sendall("b".encode("utf-8"))
                length = s.recv(2)
                length = s.recv(100)
                length = int.from_bytes(length, byteorder="big")
                s.sendall("OK".encode("utf-8"))
                temp = s.recv(length).decode("utf-8")
                temp = jsonpickle.decode(temp)
            except Exception as e:
                print("*Could not get blockchain from {}; {}".format(peer, e))
            if len(temp) > len(blockchain):
                blockchain = temp
        self.miner.blockchain = blockchain

    def get_ledger(self):
        ledger = []
        for peer in self.peer.peers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            temp = []
            try:
                s.connect((peer, self.peer.port))
                s.sendall("l".encode("utf-8"))
                length = s.recv(2)
                length = s.recv(100)
                length = int.from_bytes(length, byteorder="big")
                s.sendall("OK".encode("utf-8"))
                temp = s.recv(length).decode("utf-8")
                temp = jsonpickle.decode(temp)
            except:
                print("*Could not get ledger from {}".format(peer))
            if len(temp) > len(ledger):
                ledger = temp
        self.miner.ledger = ledger

    def test_gettx(self):
        input_value = random.randint(1, 100)
        output_value = str(random.randint(1, input_value))
        input_value = str(input_value)

        transactions = [Transaction([TXInput("a", input_value, "a")], [TXOutput(output_value, "b")])]
        transactions += [Transaction([TXInput("b", input_value, "b")], [TXOutput(output_value, "c")])]
        transactions += [Transaction([TXInput("c", input_value, "c")], [TXOutput(output_value, "d")])]
        transactions += [Transaction([TXInput("d", input_value, "d")], [TXOutput(output_value, "e")])]
        transactions += [Transaction([TXInput("e", input_value, "e")], [TXOutput(output_value, "f")])]
        return transactions

    def client(self):
        # used to mine and send requests and payloads
        # acquire lock before mining ONE iteration; check for changes after getting the lock
        if self.peer.peers == []:
            self.miner.create_blockchain()
            self.miner.create_ledger()
            print("WAITING FOR PEERS...")
        else:
            self.get_blockchain()
            self.get_ledger()
        while self.peer.peers == []:
            pass
        while True:
            transactions = self.test_gettx()

            tree = Merkle(transactions)
            candidate_header = BlockHeader(self.miner.hash_block(self.miner.blockchain[-1]),
                                           tree.get_root(), self.miner.get_timestamp(), 0)
            candidate = Block(candidate_header, transactions)
            while True:
                self.lock.acquire()
                if self.miner.check(candidate) == True or self.changed == True:
                    break
                candidate.header.nonce += 1
                self.lock.release()
            if self.changed == False:
                print("FOUND BLOCK {}".format(candidate))
                peer_opinion = self.send_block(candidate)
                if peer_opinion == True:
                    print("^^^PEERS ACCEPTED THE BLOCK^^^")
                    self.miner.save_block(candidate)
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
            i = 0
            count = 0
            while i < len(self.peer.peers):
                self.lock.acquire()
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
                self.lock.release()
                pc.close()
                sleep(5)
            sleep(3)

    def ping(self):
        pserver = threading.Thread(target = self.pings)
        pclient = threading.Thread(target = self.pingc)
        pserver.start()
        pclient.start()

    def start(self):
        t_server = threading.Thread(target = self.server)
        t_server.start()
        t_client = threading.Thread(target = self.client())
        t_client.start()
        self.ping()

if __name__ == "__main__":
    app = App()
    while True:
        pass
