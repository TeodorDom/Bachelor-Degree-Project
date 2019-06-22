from Crypto.Util import number
from functools import reduce
import bitstring

class MP_RSA:
    def __init__(self, bit_length):
        self.e = pow(2, 16) + 1
        phi = self.e
        while phi % self.e == 0:
            self.p = number.getPrime(bit_length)
            self.q = number.getPrime(bit_length)
            self.r = number.getPrime(bit_length)
            phi = (self.p - 1) * (self.q - 1) * (self.r - 1)

        self.n = self.p * self.q * self.r
        self.d = number.inverse(self.e, phi)

    def sign(self, text):
        value = bitstring.BitArray(bytes=text.encode("utf-8")).uint

        mp = pow(value % self.p, self.d % (self.p - 1), self.p)
        mq = pow(value % self.q, self.d % (self.q - 1), self.q)
        mr = pow(value % self.r, self.d % (self.r - 1), self.r)

        m = [self.p, self.q, self.r]
        b = [mp, mq, mr]
        x = [mp, 0, 0]

        for i in range(2):
            m_temp = reduce(lambda a, b: a * b, m[:i + 1])
            alpha = number.inverse(m_temp, m[i + 1])
            alpha = (alpha * (b[i + 1] - x[i])) % m[i + 1]
            x[i + 1] = (x[i] + alpha * m_temp)

        return [x[2], self.n]

    @staticmethod
    def extract(timestamp):
        ts = [int(timestamp[0]), int(timestamp[0])]
        value = pow(ts[0], pow(2, 16) + 1, ts[1])
        print("VALUE {}".format(value))
        bs = bitstring.BitArray(uint = value, length = 256)
        value = bs.bytes.decode("utf-8").replace("\x00", "")
        return value

if __name__ == "__main__":
    import time
    mp = MP_RSA(512)
    s = mp.sign(str(time.time()))
    print(s)
    print(MP_RSA.extract(s))
