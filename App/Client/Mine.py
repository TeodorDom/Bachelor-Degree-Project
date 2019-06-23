from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Utils.Merkle import *
from App.Utils.RSA import MP_RSA
from App.Utils.SocketOp import SocketOp
import socket
import random
import jsonpickle

class Miner:
    def __init__(self):
        # self.sha = SHA_1()
        self.blockchain = []
        self.ledger = []

        self.timestamp_server = ("192.168.50.8", 65432)
        self.no_bits = 6
        self.orphan_tx = []
        self.max_orphan_tx = 5

        self.wallet = Wallet()

        if path.exists("ledger"):
            self.load_ledger()
        if path.exists("blockchain"):
            self.load_blockchain()

        self.explore()

    def load_ledger(self):
        print("LOADING LEDGER")
        with open("ledger", "rb") as f:
            self.ledger = pickle.load(f)
        # self.explore()

    def save_ledger(self):
        print("SAVING LEDGER")
        with open("ledger", "wb") as f:
            pickle.dump(self.ledger, f)

    def create_ledger(self):
        print("CREATING LEDGER")
        self.save_ledger()

    def load_blockchain(self):
        print("LOADING BLOCKCHAIN")
        with open("blockchain", "rb") as f:
            self.blockchain = pickle.load(f)

    def save_blockchain(self):
        print("SAVING BLOCKCHAIN")
        with open("blockchain", "wb") as f:
            pickle.dump(self.blockchain, f)

    def create_blockchain(self):
        print("CREATING BLOCKCHAIN")
        self.genesis()
        self.save_blockchain()

    def get_timestamp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.timestamp_server)
        size = s.recv(100).decode("utf-8")
        size = int(size)
        s.sendall("OK".encode("utf-8"))
        ts = SocketOp.recv(size, s)
        ts = jsonpickle.decode(ts)
        ts = [str(ts[0]), str(ts[1])]
        # print("TS {}".format(ts))
        return ts

    def hamming(self, bits):
        return bits.count("0")

    def hash_block(self, block):
        sha = SHA_1()
        result = ""
        result += block.header.prevblock
        result += block.header.merkle
        # result += block.header.timestamp[0]
        # result += block.header.timestamp[1]
        result += MP_RSA.extract(block.header.timestamp)
        result += str(block.header.nonce)
        return sha.digest(result)

    def hash_transaction(self, tx, output_index):
        sha = SHA_1()
        result = ""
        for tx_input in tx.inputs:
            result += tx_input.hash
            result += tx_input.amount
            result += tx_input.address
        result = sha.digest(result)
        # result += tx.timestamp[0]
        # result += tx.timestamp[1]
        result += str(MP_RSA.extract(tx.timestamp))
        result += tx.outputs[output_index].amount
        result += tx.outputs[output_index].address

        return sha.digest(result)

    def save_block(self, block):
        block.header.nonce = str(block.header.nonce)
        self.blockchain.append(block)
        self.ledger += block.transactions
        self.save_blockchain()
        self.save_ledger()

    def check(self, block):
        temp = self.hash_block(block)
        print("BLOCK HASH {}".format(temp))
        if self.hamming(SHA_1.get_bits(self.no_bits, temp)) == self.no_bits:
            return True
        return False

    def genesis(self):
        transactions = [Transaction([TXInput("a","1","a")], [TXOutput("0.2","b")], self.get_timestamp())]
        tree = Merkle(transactions)
        candidate_header = BlockHeader("0" * 40, tree.get_root(), self.get_timestamp(), 0)
        candidate = Block(candidate_header, transactions)

        while self.check(candidate) == False:
            candidate.header.nonce += 1

        print("GENESIS BLOCK, NONCE {}".format(candidate.header.nonce))
        self.save_block(candidate)

    def genesis_tx(self):
        sha = SHA_1()
        return Transaction([], [TXOutput("50", sha.digest(self.wallet.w_key))], self.get_timestamp())

    def check_sum(self, tx):
        # print(tx)
        s_inputs = 0
        for tx_input in tx.inputs:
            s_inputs += int(tx_input.amount)

        s_outputs = 0
        for output in tx.outputs:
            s_outputs += int(output.amount)

        if s_outputs > s_inputs:
            return False

        return True

    def check_hash(self, tx, transactions):
        for tx_input in tx.inputs:
            index = -1
            tx_hash = tx_input.hash
            for i in range(len(transactions)-1, -1, -1):
                if tx_hash in map(lambda tx_i: tx_i.hash, transactions[i].inputs):
                    if index == -1:
                        print("FOUND AS INPUT")
                        index = i
                    else:
                        print("DOUBLE INPUT")
                        return False
                for j in range(transactions[i].no_o):
                    hash = self.hash_transaction(transactions[i], j)
                    print("CHECKING {} WITH {}".format(tx_hash, hash))
                    if tx_hash == hash and index == -1:
                        print("FOUND INDEX")
                        index = i
                    elif tx_hash == hash:
                        print("DOUBLE INDEX")
                        return False
            if index == -1:
                return False
        return True

    def add_orphan(self, tx):
        if len(self.orphan_tx) >= self.max_orphan_tx:
            position = random.randint(0, self.max_orphan_tx - 1)
            del self.orphan_tx[position]
        self.orphan_tx.append(tx)

    def verify_tx(self, tx, transactions):
        print("CHECKING TX")
        print("INPUTS")
        for txi in tx.inputs:
            print(txi.hash)
            print(txi.amount)
            print(txi.address)
        print("OUTPUTS")
        for txi in tx.outputs:
            print(txi.amount)
            print(txi.address)
        print("$$$1")
        if self.check_sum(tx) == False:
            return False
        print("$$$2")
        if self.check_hash(tx, transactions) == False:
            return False
        print("VERIFIED")
        return True

    def create_block(self, tx):
        transactions = []
        transactions.append(self.genesis_tx())
        for transaction in tx:
            if transaction.no_i != 0 and transaction.inputs != [] and self.verify_tx(transaction, self.ledger) == True:
                print("Appending tx")
                transactions.append(transaction)
            else:
                self.add_orphan(transaction)

        i = 0
        while i < len(self.orphan_tx):
            print("ORPHAN CHECK {}".format(i))
            transaction = self.orphan_tx[i]
            print(transaction)
            if transaction.no_i != 0 and transaction.inputs != [] and self.verify_tx(transaction, transactions) == True:
                print("Appending orphan")
                transactions.append(transaction)
                del self.orphan_tx[i]
            else:
                i += 1

        tree = Merkle(transactions)
        header = BlockHeader(self.hash_block(self.blockchain[-1]),
                            tree.get_root(), self.get_timestamp(), 0)
        return Block(header, transactions)

    def explore(self):
        print("BC LENGTH {}".format(len(self.blockchain)))
        for tx in self.ledger:
            print("INPUTS")
            for txi in tx.inputs:
                print(txi.hash)
                print(txi.amount)
                print(txi.address)
            print("OUTPUTS")
            for txi in tx.outputs:
                print(txi.amount)
                print(txi.address)
            print("HASH")
            for i in range(tx.no_o):
                print(self.hash_transaction(tx, i))
