from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Client.Datatypes import *

class Merkle:
    def __init__(self, leaves):
        self.set_leaves(leaves)

    def set_leaves(self, leaves):
        self.leaves = leaves
        self.generate_tree()

    def hash_transaction(self, tx):
        sha = SHA_1()
        result = ""
        result += str(tx.no_i)
        for i in tx.inputs:
            result += i.hash
            result += i.amount
            result += i.address
        result = sha.digest(result)

        result += str(tx.no_o)
        for i in tx.outputs:
            result += i.amount
            result += i.address
        result += tx.timestamp[0]
        result += tx.timestamp[1]
        return sha.digest(result)

    def generate_tree(self):
        sha = SHA_1()
        tree = []
        tree.append(list(map(lambda tx: self.hash_transaction(tx), self.leaves)))
        if len(self.leaves) % 2 == 1:
            previous = 0
        else:
            previous = None
        level = 0
        while len(tree[level]) != 1:
            level += 1
            tree.append([])
            length = len(tree[level - 1])
            if length % 2 == 1:
                length -= 1
            for i in range(0, length, 2):
                tree[level].append(sha.digest(tree[level - 1][i] + tree[level - 1][i + 1]))
            if len(tree[level]) % 2 == 1:
                if previous is None:
                    previous = level
                else:
                    tree[level].append(tree[previous][-1])
                    tree[previous] = tree[previous][:-1]
                    previous = None
        self.tree = tree
        self.height = len(tree)

    def get_root(self):
        return self.tree[-1][0]
