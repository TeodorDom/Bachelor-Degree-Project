import pickle
from time import time
from os import path
from App.Utils.Hash import  SHA_1
from uuid import getnode

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
        self.timestamp = 0

class BlockHeader:
    def __init__(self, prevblock, merkle, nonce):
        self.prevblock = prevblock
        self.merkle = merkle
        self.timestamp = 0
        self.nonce = nonce

class Block:
    def __init__(self, header, no_tx, transactions):
        self.header = header
        self.no_tx = no_tx
        self.transactions = transactions

class Wallet:
    def __init__(self):
        if path.exists("wallet"):
            self.load_wallet()
        else:
            self.create_wallet()
        print(self.w_key, self.tx_log)

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

if __name__ == "__main__":
    w = Wallet()