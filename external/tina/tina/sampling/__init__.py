'''
sampling, generating random numbers for monte-carlo intergration
'''

from tina.common import *


@ti.func
def wanghash(x):
    value = ti.cast(x, ti.u32)
    value = (value ^ 61) ^ (value >> 16)
    value *= 9
    value ^= value << 4
    value *= 0x27d4eb2d
    value ^= value >> 15
    return int(value)


@ti.func
def wanghash2(x, y):
    value = wanghash(x)
    value = wanghash(y ^ value)
    return value


@ti.func
def wanghash3(x, y, z):
    value = wanghash(x)
    value = wanghash(y ^ value)
    value = wanghash(z ^ value)
    return value


@ti.func
def unixfasthash(x):
    value = ti.cast(x, ti.u32)
    value = (value * 7**5) % (2**31 - 1)
    return int(value)


@ti.pyfunc
def binaryreverse(i):
    j = 0
    k = 1
    while i != 0:
        k <<= 1
        j <<= 1
        j |= i & 1
        i >>= 1
    return j / k


@ti.data_oriented
class RNGProxy:
    def __init__(self, data, i):
        self.data = data
        self.i = ti.expr_init(i)
        self.j = ti.expr_init(0)

    @ti.func
    def random(self):
        ret = self.data[self.i, self.j]
        self.j += 1
        return ret


@ti.data_oriented
class RNGShift:
    def __init__(self, rng, shift):
        self.rng = rng
        self.shift = ti.expr_init(shift)

    @ti.func
    def random(self):
        return (self.rng.random() + self.shift) % 1
