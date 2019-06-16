from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Utils.Merkle import *
import socket
import random

class Miner:
    def __init__(self):
        # self.sha = SHA_1()
        self.blockchain = []
        self.ledger = []

        self.timestamp_server = ("192.168.50.8", 65432)
        self.no_bits = 6
        self.orphan_tx = []
        self.max_orphan_tx = 10

        self.wallet = Wallet()

        if path.exists("ledger"):
            self.load_ledger()
        if path.exists("blockchain"):
            self.load_blockchain()

    def load_ledger(self):
        print("LOADING LEDGER")
        with open("ledger", "rb") as f:
            self.ledger = pickle.load(f)

    def save_ledger(self):
        print("SAVING LEDGER")
        with open("ledger", "wb") as f:
            pickle.dump(self.ledger, f)

    def create_ledger(self):
        print("CREATING LEDGER")
        # will require interaction with the timestamp server
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
        # will require interaction with the timestamp server
        self.genesis()
        self.save_blockchain()

    def get_timestamp(self):
        # will require interaction with the timestamp server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.timestamp_server)
        data = s.recv(100).decode("utf-8")
        print("TS: {}".format(data))
        return data

    def hamming(self, bits):
        return bits.count("0")

    def hash_block(self, block):
        sha = SHA_1()
        result = ""
        result += block.header.prevblock
        result += block.header.merkle
        result += block.header.timestamp
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

        result += tx.outputs[output_index].amount
        result += tx.outputs[output_index].address

        return sha.digest(result)

    def save_block(self, block):
        block.header.nonce = str(block.header.nonce)
        self.blockchain.append(block)
        self.save_blockchain()

    def check(self, block):
        temp = self.hash_block(block)
        # print("BLOCK HASH {}".format(temp))
        if self.hamming(SHA_1.get_bits(self.no_bits, temp)) == self.no_bits:
            return True
        return False

    def genesis(self):
        transactions = [Transaction([TXInput("a","1","a")], [TXOutput("0.2","b")], self.get_timestamp())]
        tree = Merkle(transactions)
        candidate_header = BlockHeader("0" * 40, tree.get_root(), self.get_timestamp(), 0)
        candidate = Block(candidate_header, transactions)

        while self.check(candidate) == False:
            # print("NONCE {}".format(candidate.header.nonce))
            candidate.header.nonce += 1

        print("GENESIS BLOCK, NONCE {}".format(candidate.header.nonce))
        self.save_block(candidate)

    def genesis_tx(self):
        sha = SHA_1()
        return Transaction([], [TXOutput("50", sha.digest(self.wallet.w_key))], self.get_timestamp())

    def check_sum(self, tx):
        print(tx)
        s_inputs = 0
        for tx_input in tx.inputs:
            s_inputs += int(tx_input.amount)

        s_outputs = 0
        for output in tx.outputs:
            s_outputs += int(output.amount)

        if s_outputs > s_inputs:
            return False
        return True

    def check_hash(self, tx):
        for tx_input in tx.inputs:
            index = -1
            tx_hash = tx_input.hash
            for i in range(len(self.ledger)-1, -1, -1):
                for j in range(len(self.ledger[i].no_o)):
                    hash = self.hash_transaction(self.ledger[i], j)
                    if tx_hash == hash and index == -1:
                        index = i
                    elif tx_hash == hash:
                        return False
            if index == -1:
                self.add_orphan(tx)
                return False
        return True

    def add_orphan(self, tx):
        if len(self.orphan_tx) >= self.max_orphan_tx:
            position = random.randint(0, self.max_orphan_tx - 1)
            del self.orphan_tx[position]
        self.orphan_tx.append(tx)

    def verify_tx(self, tx):
        # print("VERIFYING {}".format(tx.__dict__))
        print("$$$1")
        if self.check_sum(tx) == False:
            return False
        print("$$$2")
        if self.check_hash(tx) == False:
            return False
        return True

    def create_block(self, tx):
        transactions = []
        transactions.append(self.genesis_tx())
        for transaction in tx:
            if transaction.no_i != 0 and transaction.inputs != [] and self.verify_tx(transaction) == True:
                transactions.append(transaction)
        tree = Merkle(transactions)
        header = BlockHeader(self.hash_block(self.blockchain[-1]),
                            tree.get_root(), self.get_timestamp(), 0)
        return Block(header, transactions)

if __name__ == "__main__":
    miner = Miner()
    from Crypto.Random import random
    while True:
        input_value = random.randint(1, 100)
        output_value = str(random.randint(1, input_value))
        input_value = str(input_value)

        transactions = [Transaction([TXInput("a",input_value,"a")], [TXOutput(output_value,"b")], "0")]
        transactions += [Transaction([TXInput("b",input_value,"b")], [TXOutput(output_value,"c")], "0")]
        transactions += [Transaction([TXInput("c",input_value,"c")], [TXOutput(output_value,"d")], "0")]
        transactions += [Transaction([TXInput("d", input_value, "d")], [TXOutput(output_value, "e")], "0")]
        transactions += [Transaction([TXInput("e", input_value, "e")], [TXOutput(output_value, "f")], "0")]

        tree = Merkle(transactions)
        candidate_header = BlockHeader(miner.hash_block(miner.blockchain[-1]),
                                       tree.get_root(), miner.get_timestamp(), 0)
        candidate = Block(candidate_header, transactions)

        while miner.check(candidate) == False:
            candidate.header.nonce += 1

        print("FOUND BLOCK {}".format(candidate))
        miner.save_block(candidate)
