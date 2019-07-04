from bitstring import *

class SHA_1:
    def __init__(self):
        self.mod = pow(2, 32)
        self.K_list = [BitArray("0x5a827999"),
                       BitArray("0x6ed9eba1"),
                       BitArray("0x8f1bbcdc"),
                       BitArray("0xca62c1d6")]
        self.H = [BitArray("0x67452301"),
                BitArray("0xefcdab89"),
                BitArray("0x98badcfe"),
                BitArray("0x10325476"),
                BitArray("0xc3d2e1f0")]

    def f(self, t, x, y, z):
        if t >= 0 and t <= 19:
            return (x & y) ^ (~x & z)
        elif t >= 20 and t <= 39:
            return x ^ y ^ z
        elif t >= 40 and t <= 59:
            return (x & y) ^ (x & z) ^ (y & z)
        return x ^ y ^ z
    
    def K(self, t):
        if t >= 0 and t <= 19:
            return self.K_list[0][:]
        elif t >= 20 and t <= 39:
            return self.K_list[1][:]
        elif t >= 40 and t <= 59:
            return self.K_list[2][:]
        return self.K_list[3][:]

    def preprocess(self, text):
        padded = BitArray(bytes=text.encode("utf-8"))
        l = len(text) * 8
        k = (448 + (- l - 1) % 512) % 512
        padded = padded + [1] + [0] * k + BitArray(uint = l, length = 64)

        M = []
        for i in range(len(padded) // 512):
            M.append(padded[i * 512:(i + 1) * 512])
        return M

    def add(self, a, b):
        return BitArray(uint = (a.uint + b.uint) % self.mod, length = 32)

    def digest(self, text):
        M = self.preprocess(text)
        for i in range(len(M)):
            W = []
            for t in range(16):
                W.append(M[i].copy()[t * 32:(t + 1) * 32])
            for t in range(16, 80):
                W.append(W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16])
                W[t].rol(1)

            a = self.H[0][:]
            b = self.H[1][:]
            c = self.H[2][:]
            d = self.H[3][:]
            e = self.H[4][:]

            for t in range(80):
                T = a[:]
                T.rol(5)
                T = self.add(T, self.f(t, b, c, d))
                T = self.add(T, e)
                T = self.add(T, self.K(t))
                T = self.add(T, W[t])
                e = d
                d = c
                c = b
                c.rol(30)
                b = a
                a = T

            self.H[0] = self.add(a, self.H[0])
            self.H[1] = self.add(b, self.H[1])
            self.H[2] = self.add(c, self.H[2])
            self.H[3] = self.add(d, self.H[3])
            self.H[4] = self.add(e, self.H[4])

        result = []
        for i in range(5):
            result = result + self.H[i]

        return result.hex

    @staticmethod
    def get_bits(n, hash):
        temp = BitArray("0x" + hash)
        return str(temp[:n])[2:]
