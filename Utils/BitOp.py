
class Bits:
    def __init__(self, string, char_length = None):
        if char_length is None:
            self.bits = list(map(lambda x: int(x), string))
        else:
            self.bits = []
            for char in string:
                self.bits += self.binary(ord(char), char_length)
        # print(self.bits)
    
    def binary(self, char, blength):
        result = []
        for bit in range(blength):
            result.append(char % 2)
            char //= 2
        # print(result)
        return list(reversed(result))
    
    def __lshift__(self, other):
        return Bits(self.bits[other:] + [0] * other)

    def __rshift__(self, other):
        return Bits([0] * other + self.bits[:-other])

    def __invert__(self):
        self.bits = Bits(list(map(lambda x: 1 - x, self.bits)))

    def __and__(self, other):
        l = len(self.bits)
        if l != len(other.bits):
            raise ValueError("The bitstring lengths need to match")
        result = [0] * l
        for i in range(len(self.bits)):
            if self.bits[i] + other.bits[i] == 2:
                result[i] = 1
        return Bits(result)
    
    def __or__(self, other):
        l = len(self.bits)
        if l != len(other.bits):
            raise ValueError("The bitstring lengths need to match")
        result = [0] * l
        for i in range(len(self.bits)):
            if self.bits[i] + other.bits[i] >= 1:
                result[i] = 1
        return Bits(result)
    
    def __xor__(self, other):
        l = len(self.bits)
        if l != len(other.bits):
            raise ValueError("The bitstring lengths need to match")
        result = [0] * l
        for i in range(len(self.bits)):
            if self.bits[i] + other.bits[i] == 1:
                result[i] = 1
        return Bits(result)
        
    def rotl(self, n):
        return self.bits[n:] + self.bits[:n]

    def __add__(self, other):
        len1 = len(self.bits)
        len2 = len(other.bits)
        if len1 != len2:
            raise ValueError("The bitstring lengths need to match")
        result = [0] * len1
        for i in range(len1 - 1, 0, -1):
            result[i] = result [i] + self.bits[i] + other.bits[i]
            if result[i] >= 2:
                result[i - 1] += 1
                result[i] -= 2
        if result[0] >= 2:
            result[1] -= 2
        return Bits(result)

def test():
    a = Bits("abc", 8)
    b = Bits("abd", 8)
    c = Bits("acd", 8)
    print((a ^ b ^ c).bits)
    print("& {}".format(a & b))
    print("| {}".format(a | b))
    print("^ {}".format(a ^ b))
    print("shift st {}".format(a << 3))
    print("shift dr {}".format(a >> 3))
    print("rotl {}".format(a.rotl(3)))

if __name__ == '__main__':
    test()