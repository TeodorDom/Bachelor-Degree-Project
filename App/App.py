from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.dirname(__file__), "..")))

import jsonpickle
from copy import deepcopy
import bitstring as bs
from App.Client.Mine import *
from App.Network.Peer import *
from time import sleep
import threading
import random

class App:
    def __init__(self):
        self.lock = threading.Semaphore(4)
        self.miner = Miner()
        self.peer = Peer()
        self.changed = False
        self.tx_address = ("192.168.50.9", 65431)

        self.ps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ps.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ping_port = 65433
        self.ps.bind((self.peer.address, self.ping_port))

        self.start()

    def verify_transaction(self, tx):
        return True

    def check_block(self, block):
        prev_block = self.miner.hash_block(self.miner.blockchain[-1])
        print("##1")
        if block.header.prevblock != prev_block:
            print("EXPECTED {}".format(prev_block))
            print("GOT {}".format(block.header.prevblock))
            return False
        print("##2")
        if float(self.miner.get_timestamp()) < float(block.header.timestamp):
            return False
        print("##3")
        if len(block.transactions) != block.no_tx:
            return False

        # for tx in block.transactions:
        #     print("##4")
        #     if self.verify_transaction(tx) == False:
        #         return False

        tree = Merkle(block.transactions)
        print("##5")
        if tree.get_root() != block.header.merkle:
            return False
        print("##6")
        if self.miner.check(block) == False:
            return False
        return True

    def send_block(self, block, addr):
        addr.append(self.peer.address)
        print("ADDR {}".format(addr))
        denied = 0
        no_denies = len(self.peer.peers) / 3
        for p in self.peer.peers:
            print("PEER {}".format(p))
            if p not in addr:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                response = 0
                try:
                    s.connect((p, self.peer.port))
                    s.sendall("B".encode("utf-8"))
                    response = s.recv(2)
                    data = jsonpickle.encode(addr).encode("utf-8")
                    length = len(data)
                    s.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
                    response = s.recv(2)
                    s.sendall(data)
                    response = s.recv(2)

                    data = jsonpickle.encode(block).encode("utf-8")
                    length = len(data)
                    s.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
                    response = s.recv(2)
                    s.sendall(data)
                    response = s.recv(1)
                    response = int.from_bytes(response, byteorder="big")
                except Exception as e:
                    print("CONNECTION WITH {} FAILED, {}".format(p, e))
                if response == 1:
                    break
                if response == 0:
                    denied += 1
                if denied >= no_denies:
                    return False
        return True

    def receive_block(self, conn):
        # checks received block
        # self.lock.acquire()
        self.changed = None
        print("CHECKING BLOCK")
        size = conn.recv(100)
        size = bs.BitArray(bytes = size).uint
        conn.sendall("OK".encode("utf-8"))
        addr = conn.recv(size)
        addr = jsonpickle.decode(addr.decode("utf-8"))

        conn.sendall("OK".encode("utf-8"))

        size = conn.recv(100)
        size = bs.BitArray(bytes = size).uint
        conn.sendall("OK".encode("utf-8"))
        block = conn.recv(size)
        print("BLOCK {}".format(block))
        block = jsonpickle.decode(block.decode("utf-8"))
        b = self.check_block(block)

        peer_opinion = False
        if b == True:
            peer_opinion = self.send_block(block, addr)
        self.changed = peer_opinion
        print("Change Blockchain? {}".format(peer_opinion))
        if peer_opinion == True:
            self.miner.save_block(block)
        else:
            self.get_parameter("b")
        conn.sendall(bytes([int(b)]))
        print("---BLOCKCHAIN LENGTH: {}".format(len(self.miner.blockchain)))
        # self.lock.release()

    def inactive(self, addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.peer.boot_peer)
        s.sendall("I".encode("utf-8"))
        s.sendall(addr.encode("utf-8"))

    def get_transactions(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.tx_address)
        size = s.recv(100)
        size = int.from_bytes(size, byteorder="big")
        s.sendall("OK".encode("utf-8"))
        tx = s.recv(size)
        tx = jsonpickle.decode(tx.decode("utf-8"))
        return tx

    def send_blockchain(self, conn):
        data = deepcopy(self.miner.blockchain)
        data = jsonpickle.encode(data).encode("utf-8")
        length = len(data)
        conn.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
        response = conn.recv(2)
        conn.sendall(data)
        print("SENT BLOCKCHAIN")

    def send_ledger(self, conn):
        data = deepcopy(self.miner.ledger)
        data = jsonpickle.encode(self.miner.ledger).encode("utf-8")
        length = len(data)
        conn.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
        response = conn.recv(2)
        conn.sendall(data)
        print("SENT LEDGER")

    def server(self):
        options = {
            "B": self.receive_block,
            "r": self.peer.reboot,
            "b": self.send_blockchain,
            "l": self.send_ledger
        }
        print("SERVER STARTED")
        while True:
            self.peer.ss.listen(25)
            try:
                conn, addr = self.peer.ss.accept()
                self.lock.acquire()
                print("LOCK S1")
                option = conn.recv(1).decode("utf-8")
                print("CONNECTION FROM {}: {}".format(addr[0], option))
                if option == "b" and self.miner.blockchain == []:
                    conn.sendall("NO".encode("utf-8"))
                else:
                    conn.sendall("OK".encode("utf-8"))
                    options[option](conn)
                conn.close()
            except Exception as e:
                print("CONNECTION ERROR -> {}".format(option))
                print("REASON {}".format(e))
            self.lock.release()
            sleep(0.6)

    def get_parameter(self, option):
        blockchain = []
        i = 0
        while i < len(self.peer.peers):
            length = "NO"
            temp = []
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((self.peer.peers[i], self.peer.port))
                s.sendall(option.encode("utf-8"))
                length = s.recv(2).decode("utf-8")

                while length == "NO":
                    print("{} DOES NOT HAVE AN ANSWER FOR {} YET".format(self.peer.peers[i], option))
                    sleep(6)

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(10)
                    s.connect((self.peer.peers[i], self.peer.port))
                    s.sendall(option.encode("utf-8"))
                    length = s.recv(2).decode("utf-8")
                length = s.recv(100)
                length = bs.BitArray(bytes=length).uint
                s.sendall("OK".encode("utf-8"))
                temp = s.recv(length).decode("utf-8")
                temp = jsonpickle.decode(temp)
                i += 1
            except Exception as e:
                print("*Could not get blockchain from {}; {}".format(self.peer.peers[i], e))
                i += 1
            if len(temp) > len(blockchain) and type(temp) is list:
                blockchain = deepcopy(temp)

        if option == "b":
            self.miner.blockchain = deepcopy(blockchain)
            self.miner.save_blockchain()
            print("---BLOCKCHAIN LENGTH: {}".format(len(self.miner.blockchain)))
        else:
            self.miner.ledger = blockchain
            self.miner.save_ledger()
            print("---LEDGER LENGTH: {}".format(len(self.miner.ledger)))

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

    def client(self):
        # used to mine and send requests and payloads
        # acquire lock before mining ONE iteration; check for changes after getting the lock
        self.lock.acquire()
        if self.peer.peers == []:
            if self.miner.blockchain == []:
                self.miner.create_blockchain()
            if self.miner.ledger == []:
                self.miner.create_ledger()
            print("WAITING FOR PEERS...")
        else:
            self.get_parameter("b")
            self.get_parameter("l")
        self.lock.release()
        while self.peer.peers == []:
            pass
        while True:
            if self.peer.peers != []:
                try:
                    while self.miner.blockchain == []:
                        self.get_parameter("b")
                    # transactions = []
                    # transactions.append(self.miner.genesis_tx())
                    transactions = self.get_transactions()

                    candidate = self.miner.create_block(transactions)
                    while True:
                        if self.changed is False:
                            self.lock.acquire(timeout=5)
                            print("LOCK C1")
                            if self.miner.check(candidate) == True or self.changed == True:
                                break
                            candidate.header.nonce += 1
                            self.lock.release()
                        sleep(0.25)
                    self.lock.acquire(timeout=10)
                    print("LOCK C2")
                    if self.changed == False:
                        print("FOUND BLOCK {}".format(self.miner.hash_block(candidate)))
                        print("PREVIOUS: H {} BC {}".format(candidate.header.prevblock, self.miner.hash_block(self.miner.blockchain[-1])))
                        sleep(random.randint(1, 5))
                        peer_opinion = False
                        if self.changed == False:
                            peer_opinion = self.send_block(candidate, [])
                        if peer_opinion == True:
                            print("^^^PEERS ACCEPTED THE BLOCK^^^")
                            self.miner.save_block(candidate)
                        else:
                            print("^^^PEERS REJECTED THE BLOCK^^^")
                            self.get_parameter("b")
                        self.changed = False
                    self.lock.release()
                except Exception as e:
                    print("CLIENT ERROR: {}".format(e))
            else:
                print("ONLY PEER")
                sleep(10)

    def pings(self):
        while True:
            if self.changed == False:
                self.lock.acquire(timeout=10)
                print("LOCK PS")
                self.ps.listen(50)
                conn, addr = self.ps.accept()
                print("PING FROM {}".format(addr))
                option = conn.recv(1).decode("utf-8")
                conn.sendall("OK".encode("utf-8"))
                conn.close()
                self.lock.release()
                sleep(2)

    def pingc(self):
        while True:
            i = 0
            count = 0
            while i < len(self.peer.peers):
                if self.changed is False:
                    self.lock.acquire(timeout=10)
                    print("LOCK PC")
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
                        if count >= 3:
                            self.inactive(self.peer.peers[i])
                            count = 0
                            i += 1
                    pc.close()
                    self.lock.release()
                sleep(5)
            sleep(7)

    def start(self):
        t_server = threading.Thread(target = self.server)
        t_server.start()
        p_server = threading.Thread(target = self.pings)
        p_server.start()
        p_client = threading.Thread(target = self.pingc)
        p_client.start()
        t_client = threading.Thread(target = self.client())
        t_client.start()

if __name__ == "__main__":
    app = App()

