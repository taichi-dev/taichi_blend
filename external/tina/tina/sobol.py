import numpy as np


# https://web.maths.unsw.edu.au/~fkuo/sobol/
def NumpySobol(N, D):
    print(f'[TinaSobol] reading data from file...')
    f = open('/home/bate/Downloads/new-joe-kuo-6.21201')
    f.readline()

    print(f'[TinaSobol] initializing with N={N}, D={D}')

    L = int(np.ceil(np.log2(N)))

    def C(i):
        bits = 1
        value = i
        while value & 1:
            value >>= 1
            bits += 1
        return bits

    V = np.full((L + 1, D), 0)

    for j in range(D):
        if j != 0:
            _, s, a, M = f.readline().split(maxsplit=3)
            s, a = int(s), int(a)
            m = np.full(s + 1, 0)
            for i, M in enumerate(map(int, M.split())):
                m[i + 1] = M
        else:
            m = np.full(L + 1, 1)
            s = L

        if L <= s:
            for i in range(L + 1):
                V[i, j] = m[i] << (32 - i)
        else:
            for i in range(s + 1):
                V[i, j] = m[i] << (32 - i)
            for i in range(s + 1, L + 1):
                V[i, j] = V[i - s, j] ^ (V[i - s, j] >> s)
                for k in range(1, s):
                    V[i, j] ^= ((a >> (s - 1 - k)) & 1) * V[i - k, j]

    print(f'[TinaSobol] start generating sequence')

    X = np.full(D, 0)
    for i in range(N):
        P = X / 2**32
        X = X ^ V[C(i), :]
        yield P


import taichi as ti


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
class TaichiSobol:
    def __init__(self, dim=21201, nsamples=2**20, skip=17):
        self.dim = dim
        self.nsamples = nsamples
        self.skip = skip
        self.data = ti.field(float, self.dim)
        self.reset()

    def reset(self):
        self.core = NumpySobol(self.nsamples, self.dim)
        for i in range(self.skip):
            next(self.core)

    def update(self):
        arr = next(self.core)
        self.data.from_numpy(arr)

    @ti.func
    def calc(self, x):
        return self.data[x % self.dim]

    def get_proxy(self, x):
        return self.Proxy(self, x)

    @ti.data_oriented
    class Proxy:
        def __init__(self, sobol, x):
            self.sobol = sobol
            self.x = ti.expr_init(x)
            self.y = ti.expr_init(0)

        @ti.func
        def random(self):
            ret = self.sobol.calc(wanghash2(self.x, self.y))
            self.y += 1
            return ret


if __name__ == '__main__':
    n = 128
    sobol1 = TaichiSobol(1024)
    sobol2 = TaichiSobol(1024)
    img1 = ti.field(float, (n, n))
    img2 = ti.field(float, (n, n))
    img3 = ti.field(float, (n, n))


    @ti.kernel
    def render_image():
        for i, j in ti.ndrange(n, n):
            id = wanghash2(i, j)
            so = sobol1.get_proxy(id)
            img1[i, j] += so.random()
            img2[i, j] += sobol2.calc(id)
            img3[i, j] += ti.random()


    gui1 = ti.GUI('sobol+hash')
    gui2 = ti.GUI('sobol')
    gui3 = ti.GUI('pseudo')
    gui1.fps_limit = 10
    gui2.fps_limit = 10
    gui3.fps_limit = 10
    while gui1.running and gui2.running and gui3.running:
        sobol1.update()
        sobol2.update()
        render_image()
        gui1.set_image(ti.imresize(img1.to_numpy() / (1 + gui1.frame), 512))
        gui2.set_image(ti.imresize(img2.to_numpy() / (1 + gui2.frame), 512))
        gui3.set_image(ti.imresize(img3.to_numpy() / (1 + gui3.frame), 512))
        gui1.show()
        gui2.show()
        gui3.show()
