import socket

class SocketOp:

    @staticmethod
    def send(data, conn):
        length = len(data)
        sent = 0
        while sent < length:
            actual = conn.send(data[sent:])
            sent += actual
            if actual == 0:
                break

    @staticmethod
    def recv(length, conn):
        temp = bytes()
        while len(temp) < length:
            recvd = conn.recv(length)
            temp += recvd
            if recvd == 0:
                break
        return temp.decode("utf-8")
