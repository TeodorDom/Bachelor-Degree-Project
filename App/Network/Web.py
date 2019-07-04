from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Client.Datatypes import *
from App.Utils.SocketOp import SocketOp
from flask import Flask, Response, request
from flask_cors import CORS, cross_origin
import socket
import jsonpickle
import json
import threading
from time import sleep

class Web:
    def __init__(self):
        self.lock = threading.Lock()
        self.timestamp_server = ("192.168.50.8", 65432)
        self.boot_peer = ("192.168.50.10", 65434)

        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind(("192.168.50.9", 65431))
        self.max_tx = 5
        self.tx_queue = []
        self.peers = []
        self.ledger = []

        t = threading.Thread(target=self.tx_server)
        w = threading.Thread(target=self.web_server)
        t.start()
        w.start()

    def get_timestamp(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.timestamp_server)
        size = s.recv(100).decode("utf-8")
        size = int(size)
        s.sendall("OK".encode("utf-8"))
        ts = SocketOp.recv(size, s)
        ts = jsonpickle.decode(ts)
        ts = [str(ts[0]), str(ts[1])]
        return ts

    def get_peers(self):
        peers = []
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.boot_peer)
            self.address = s.getsockname()[0]
            s.send("P".encode("utf-8"))
            length = s.recv(100)
            length = int.from_bytes(length, byteorder="big")
            s.send("OK".encode("utf-8"))
            peers = SocketOp.recv(length, s)
            peers = json.loads(peers)
            print("PEERS: {}".format(peers))
            s.close()
        except Exception as e:
            print("BOOT PEER CONNECTION ERROR")
            print(e)
        if peers == "ONLY PEER":
            peers = []
        self.peers = peers

    def get_ledger(self):
        self.lock.acquire()
        blockchain = []
        i = 0
        while i < len(self.peers):
            temp = []
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.peers[i], 65434))
                s.sendall("b".encode("utf-8"))
                length = s.recv(2).decode("utf-8")

                while length == "NO":
                    print("{} DOES NOT HAVE AN ANSWER FOR {} YET".format(self.peers[i], "b"))
                    sleep(6)

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((self.peers[i], 65434))
                    s.sendall("b".encode("utf-8"))
                    length = s.recv(2).decode("utf-8")

                length = s.recv(100).decode("utf-8")
                length = int(length)
                s.sendall("OK".encode("utf-8"))
                temp = SocketOp.recv(length, s)
                print("RECEIVED: {}".format(len(temp)))
                temp = jsonpickle.decode(temp)
                print("DECODED!")
                i += 1
                s.close()
            except Exception as e:
                print("*Could not get ledger from {}; {}".format(self.peers[i], e))
                i += 1
            if len(temp) > len(blockchain) and type(temp) is list:
                blockchain = temp[:]

        ledger = []
        for block in blockchain:
            ledger += block.transactions

        if len(ledger) > len(self.ledger):
            self.ledger = ledger
        print("---LEDGER LENGTH: {}".format(len(self.ledger)))
        self.lock.release()

    def web_server(self):
        app = Flask(__name__)
        CORS(app, support_credentials=True)

        def create_tx(body):
            inputs = []
            for i in range(int(body["no_i"])):
                temp = body["inputs"][i]
                inputs.append(TXInput(temp["tx_hash"], temp["amount"], temp["address"]))
                # print(inputs[i].__dict__)

            outputs = []
            for i in range(int(body["no_o"])):
                temp = body["outputs"][i]
                outputs.append(TXOutput(temp["amount"], temp["address"]))
                # print(outputs[i].__dict__)
            return Transaction(inputs, outputs, self.get_timestamp())

        @app.route("/transaction", methods=["POST"])
        @cross_origin(supports_credentials=True)
        def add_transaction():
            try:
                body = request.get_json()
                print(body)
                self.tx_queue.append(create_tx(body))
                # print(self.tx_queue[-1].__dict__)
                return Response(status=200)
            except:
                print("INVALID TRANSACTION FORMAT")
                return Response(status=400)

        @app.route("/check", methods=["POST"])
        @cross_origin(supports_credentials=True)
        def check_transaction():
            try:
                body = request.get_json()
                print(body)
                tx = create_tx(body)
                self.lock.acquire()
                found = 0
                for index in range(len(self.ledger) - 1, -1, -1):
                    if (self.ledger[index].no_i == tx.no_i and
                            (self.ledger[index].no_o == tx.no_o or self.ledger[index].no_o == tx.no_o + 1)):
                        found = 0
                        temp = 0
                        for i in range(tx.no_i):
                            if (
                                tx.inputs[i].hash == self.ledger[index].inputs[i].hash and
                                tx.inputs[i].amount == self.ledger[index].inputs[i].amount and
                                tx.inputs[i].address == self.ledger[index].inputs[i].address
                            ):
                                temp += 1
                        if temp == self.ledger[index].no_i:
                            found += 1

                        temp = 0
                        for i in range(tx.no_o):
                            if (
                                tx.outputs[i].amount == self.ledger[index].outputs[i].amount and
                                tx.outputs[i].address == self.ledger[index].outputs[i].address
                            ):
                                temp += 1
                        if temp == self.ledger[index].no_o or temp + 1 == self.ledger[index].no_o:
                            found += 1
                        if found == 2:
                            break
                self.lock.release()
                if found == 2:
                    return Response(status=200, response="VERIFIED")
                return Response(status=404, response="NOT VERIFIED")

            except:
                print("INVALID TRANSACTION FORMAT")
                return Response(status=400, response="MALFORMED")
        app.run(host="192.168.50.9", port=65430)

    def tx_server(self):
        print("WEB SERVER STARTED")
        while True:
            try:
                self.get_peers()
                self.get_ledger()
                self.ss.listen(50)
                conn, addr = self.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                data = self.tx_queue[ :self.max_tx]
                data = jsonpickle.encode(data).encode("utf-8")
                length = len(data)
                SocketOp.send(str(length).encode("utf-8"), conn)
                response = conn.recv(2)
                SocketOp.send(data, conn)
                conn.close()
                self.tx_queue = self.tx_queue[self.max_tx: ]
            except Exception as e:
                print("COULD NOT SEND TRANSACTIONS")
                print(e)

if __name__ == "__main__":
    w = Web()
