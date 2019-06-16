import socket
import threading
from time import time

class Timestamp():
    def __init__(self):
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind(("192.168.50.8", 65432))
        t = threading.Thread(target = self.start)
        t.start()

    def start(self):
        print("TIMESTAMP SERVER STARTED")
        while True:
            try:
                self.ss.listen(50)
                conn, addr = self.ss.accept()
                print("CONNECTION FROM {}".format(addr[0]))
                data = str(time())
                conn.sendall(data.encode("utf-8"))
                conn.close()
            except:
                print("COULD NOT SEND TIMESTAMP")

if __name__ == "__main__":
    t = Timestamp()
