import socket
import json

class BootPeer:
    def __init__(self):
        self.port = 65434
        address = ("192.168.50.10", self.port)
        self.n = 0
        self.max_peers = pow(2, self.n)
        self.peers = []
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss.bind(address)
        self.cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_peers(self, conn, addr):
        if addr[0] not in self.peers:
            self.peers.append(addr[0])

        no_peers = len(self.peers)

        if no_peers > self.max_peers:
            self.n += 1
            self.max_peers *= 2
            # broadcast that each peer needs to get one more peer

        if no_peers == 1:
            data = "ONLY PEER"
            print("ONLY PEER")
        else:
            data = []
            index = self.peers.index(addr[0])
            for i in range(self.n):
                peer_index = (index + pow(2, i)) % self.max_peers
                while peer_index > no_peers:
                    peer_index = (peer_index + 1) % self.max_peers

                data.append(self.peers[peer_index])
        data = json.dumps(data).encode("utf-8")


        try:
            conn.sendall(bytes([len(data)]))
            response = conn.recv(2)
            conn.sendall(data)
        except:
            print("Connection error with {}".format(addr[0]))

    def remove_peer(self, addr):
        pass

    def server(self):
        while True:
            print("Listening...")
            print("PEERS: {}".format(self.peers))
            self.ss.listen(50)
            conn, addr = self.ss.accept()
            option = conn.recv(1).decode("utf-8")
            if option == "R":
                self.send_peers(conn, addr)
            else:
                self.remove_peer(addr)
            conn.close()

    def client(self):
        pass

if __name__ == "__main__":
    b = BootPeer()
    b.server()