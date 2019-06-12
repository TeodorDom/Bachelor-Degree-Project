from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Utils.Merkle import *

class Miner:
    def __init__(self):
        self.sha = SHA_1()
        if path.exists("ledger"):
            self.load_ledger()
        else:
            self.create_ledger()
        if path.exists("params"):
            self.load_params()
        else:
            self.create_params()

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
        self.ledger = []
        self.save_ledger()

    def load_params(self):
        print("LOADING PARAMS")
        with open("params", "rb") as f:
            self.blockchain = pickle.load(f)

    def save_params(self):
        print("SAVING PARAMS")
        with open("params", "wb") as f:
            pickle.dump(self.blockchain, f)

    def create_params(self):
        print("CREATING PARAMS")
        # will require interaction with the timestamp server
        self.blockchain = []
        # self.genesis()
        self.save_params()

    def get_timestamp(self):
        # will require interaction with the timestamp server
        return str(time())

    def hamming(self, bits):
        return bits.count("0")

    def hash_block(self, block):
        result = ""
        result += block.header.prevblock
        result += block.header.merkle
        result += block.header.timestamp
        result += str(block.header.nonce)
        return self.sha.digest(result)

    def save_block(self, block):
        block.header.nonce = str(block.header.nonce)
        self.blockchain.append(block)
        self.save_params()

    def check(self, block):
        """
        USAGE: Each iteration is called separately; this will be done in order to accommodate
        the network architecture, as a miner will have to stop if someone else finds a block.
        :param block:
        :param nonce:
        :return:
        """
        temp = self.hash_block(block)
        print("BLOCK HASH {}".format(temp))
        if self.hamming(self.sha.get_bits(7, temp)) == 7:
            return True
        return False

    def genesis(self):
        transactions = [Transaction([TXInput("a","1","a")], [TXOutput("0.2","b")])]
        tree = Merkle(transactions)
        candidate_header = BlockHeader("0" * 40, tree.get_root(), self.get_timestamp(), 0)
        candidate = Block(candidate_header, transactions)

        while self.check(candidate) == False:
            print("NONCE {}".format(candidate.header.nonce))
            candidate.header.nonce += 1

        print("GENESIS BLOCK, NONCE {}".format(candidate.header.nonce))
        self.save_block(candidate)

# if __name__ == "__main__":
#     from Crypto.Random import random
#     miner = Miner()
#
#     while True:
#         input_value = random.randint(1, 100)
#         output_value = str(random.randint(1, input_value))
#         input_value = str(input_value)
#
#         transactions = [Transaction([TXInput("a",input_value,"a")], [TXOutput(output_value,"b")])]
#         transactions += [Transaction([TXInput("b",input_value,"b")], [TXOutput(output_value,"c")])]
#         transactions += [Transaction([TXInput("c",input_value,"c")], [TXOutput(output_value,"d")])]
#         transactions += [Transaction([TXInput("d", input_value, "d")], [TXOutput(output_value, "e")])]
#         transactions += [Transaction([TXInput("e", input_value, "e")], [TXOutput(output_value, "f")])]
#
#         tree = Merkle(transactions)
#         candidate_header = BlockHeader(miner.hash_block(miner.blockchain[-1]),
#                                        tree.get_root(), miner.get_timestamp(), 0)
#         candidate = Block(candidate_header, transactions)
#
#         while miner.check(candidate) == False:
#             candidate.header.nonce += 1
#
#         print("FOUND BLOCK {}".format(candidate))
#         miner.save_block(candidate)
