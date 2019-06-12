from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

import pickle
from time import time
from uuid import getnode
from App.Utils.Hash import SHA_1

class TXInput:
    def __init__(self, tx, amount, address):
        self.tx = tx
        self.amount = amount
        self.address = address

class TXOutput:
    def __init__(self, amount, address):
        self.amount = amount
        self.address = address

class Transaction:
    def __init__(self, inputs, outputs):
        self.no_i = len(inputs)
        self.inputs = inputs
        self.no_o = len(outputs)
        self.outputs = outputs
        self.timestamp = "0"

class BlockHeader:
    def __init__(self, prevblock, merkle, timestamp, nonce):
        self.prevblock = prevblock
        self.merkle = merkle
        self.timestamp = timestamp
        self.nonce = nonce

class Block:
    def __init__(self, header, transactions):
        self.size = self.get_size()
        self.header = header
        self.no_tx = len(transactions)
        self.transactions = transactions

    def get_size(self):
        #TODO
        return 10

class Wallet:
    def __init__(self):
        if path.exists("wallet"):
            self.load_wallet()
        else:
            self.create_wallet()

    def load_wallet(self):
        print("LOADING WALLET")
        with open("wallet", "rb") as f:
            self.w_key, self.tx_log = pickle.load(f)

    def create_wallet(self):
        print("CREATING WALLET")
        s = SHA_1()
        self.w_key = s.digest(str(getnode()) + str(time()))
        self.tx_log = []
        self.save_wallet()

    def save_wallet(self):
        print("SAVING WALLET")
        with open("wallet", "wb") as f:
            pickle.dump([self.w_key, self.tx_log], f)

    def create_keys(self):
        #TODO
        pass

if __name__ == "__main__":
    w = Wallet()
