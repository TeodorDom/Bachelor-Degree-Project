from sys import path as spath
from os import path

spath.insert(0, path.abspath(path.join(path.join(path.dirname(__file__), ".."), "..")))

from App.Client.Datatypes import *

import socket
import jsonpickle
import random
import threading

class Web:
    def __init__(self):
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind(("192.168.50.9", 65431))
        self.max_tx = 5
        self.tx_queue = []
        for i in range(7):
            self.tx_queue += self.test_gettx()
        t = threading.Thread(target=self.tx_server)
        t.start()

    def test_gettx(self):
        input_value = random.randint(1, 100)
        output_value = str(random.randint(1, input_value))
        input_value = str(input_value)

        transactions = [Transaction([TXInput("a", input_value, "a")], [TXOutput(output_value, "b")], "0")]
        transactions += [Transaction([TXInput("b", input_value, "b")], [TXOutput(output_value, "c")], "0")]
        transactions += [Transaction([TXInput("c", input_value, "c")], [TXOutput(output_value, "d")], "0")]
        transactions += [Transaction([TXInput("d", input_value, "d")], [TXOutput(output_value, "e")], "0")]
        transactions += [Transaction([TXInput("e", input_value, "e")], [TXOutput(output_value, "f")], "0")]
        return transactions


    def tx_server(self):
        print("WEB SERVER STARTED")
        while True:
            try:
                self.ss.listen(50)
                conn, addr = self.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                data = self.tx_queue[ :self.max_tx]
                data = jsonpickle.encode(data).encode("utf-8")
                length = len(data)
                conn.sendall(length.to_bytes((length.bit_length() + 7) // 8, byteorder="big"))
                response = conn.recv(2)
                conn.sendall(data)
                conn.close()
                self.tx_queue = self.tx_queue[self.max_tx: ]
            except:
                print("COULD NOT SEND TRANSACTIONS")

if __name__ == "__main__":
    w = Web()