from App.Utils.Hash import  SHA_1
from App.Client.Datatypes import *
from os import path

class Mine:
    def __init__(self):
        if path.exists("ledger"):
            self.load_params()
        else:
            self.create_params()

    def load_params(self):
        print("LOADING LEDGER")
        with open("ledger", "rb") as f:
            self.ledger = pickle.load(f)

    def save_params(self):
        print("SAVING LEDGER")
        with open("ledger", "wb") as f:
            pickle.dump(self.ledger, f)

    def create_params(self):
        print("CREATING LEDGER")
        self.ledger = []
        self.save_params()


