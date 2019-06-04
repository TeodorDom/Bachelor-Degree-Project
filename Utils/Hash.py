from BitOp import Bits

class SHA_1:
    def f(self, t, x, y, z):
        if t >= 0 and t <= 19:
            return ((x & y) ^ (~x & z))
        elif t >= 20 and t <= 39:
            return (x ^ y ^ x)
        elif t >= 40 and t <= 59:
            return ((x & y) ^ (x & z) ^ (y & z))
        return (x ^ y ^ x)

    def preprocess(self, text):
        self.bits_obj = Bits(text, 8)
        l = len(text) * 8
        k = (448 + (- l - 1) % 512) % 512
        padded = self.bits_obj.bits + [1] + [0] * k + self.bits_obj.binary(l, 64)

        self.M = []
        for i in range(len(padded) // 512):
            self.M.append(padded[i * 512:(i + 1) * 512])
        self.H = [Bits("01100111010001010010001100000001"), 
                Bits("11101111110011011010101110001001"),
                Bits("10011000101110101101110011111110"),
                Bits("00010000001100100101010001110110"),
                Bits("11000011110100101110000111110000")]

    def digest(self, text):
        self.preprocess(text)

        for i in range(1, len(self.M)):


if __name__ == "__main__":
    s = SHA_1()
    s.preprocess("abc")
    for i in range(len(s.M)):
        print(s.M[i])
    