'''
Sobol quasi-random generator for low occupancy sequence

references: https://web.maths.unsw.edu.au/~fkuo/sobol/
'''

from tina.sampling import *


@ti.func
def count_low_bits(i):
    bits = 1
    value = i
    while value & 1:
        value >>= 1
        bits += 1
    return bits

@ti.func
def construct_float(i):
    ret = 0.0
    value = i
    term = 0.5
    while value:
        if value & clamp_unsigned(1 << 31):
            ret += term
        value <<= 1
        term *= 0.5
    return ret


def calc_sobol_vgrid(N, D):
    try:
        # https://github.com/archibate/pysobol
        from pysobol.data import _sobol_data as file
    except ImportError:
        please_install('pysobol')

    file = iter(file)

    print(f'[TinaSobol] initializing with N={N}, D={D}')

    L = int(np.ceil(np.log2(N)))

    V = np.full((L + 1, D), 0)

    for j in range(D):
        if j != 0:
            s = next(file)
            a = next(file)
            m = np.full(s + 1, 0)
            for i in range(s):
                m[i + 1] = next(file)
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

    print('[TinaSobol] sobol vgrid generated successfully')
    return V


@ti.data_oriented
class SobolSampler(metaclass=Singleton):
    def __init__(self, dim=21201, nsamples=2**20, skip=64):  # 4 MB
        self.dim = dim
        self.nsamples = nsamples
        self.skip = skip

        V = calc_sobol_vgrid(nsamples, dim)
        self.X = ti.field(int, self.dim)
        self.P = ti.field(float, self.dim)
        self.V = ti.field(int, V.shape)
        self.time = ti.field(int, ())

        @ti.materialize_callback
        def init_V():
            self.V.from_numpy(V)

        ti.materialize_callback(self.reset)

    def reset(self):
        print('[TinaSobol] reset sobol generator...')
        self.time[None] = 0
        self.X.fill(0)
        for i in range(self.skip):
            self.update()

    @ti.kernel
    def update(self):
        i = count_low_bits(self.time[None])
        self.time[None] += 1
        for j in range(self.dim):
            self.X[j] ^= self.V[i, j]
            self.P[j] = construct_float(self.X[j])

    @ti.func
    def calc(self, i):
        return self.P[i % self.dim]

    @ti.func
    def get_proxy(self, i):
        return self.Proxy(self, i)

    @ti.data_oriented
    class Proxy:
        def __init__(self, sobol, i):
            self.sobol = sobol
            self.i = ti.expr_init(i)

        @ti.func
        def random(self):
            ret = self.sobol.calc(self.i)
            self.i += 1
            return ret


if __name__ == '__main__':
    n = 128
    sobol = SobolSampler(1024)
    img1 = ti.Vector.field(3, float, (n, n))
    img2 = ti.Vector.field(3, float, (n, n))


    @ti.kernel
    def render_image():
        for i, j in ti.ndrange(n, n):
            so = sobol.get_proxy(wanghash2(i, j))
            img1[i, j] += V(so.random(), so.random(), so.random())
            img2[i, j] += V(ti.random(), ti.random(), ti.random())


    gui1 = ti.GUI('sobol')
    gui2 = ti.GUI('pseudo')
    gui2.fps_limit = gui1.fps_limit = 5
    while gui1.running and gui2.running:
        sobol.update()
        render_image()
        gui1.set_image(ti.imresize(img1.to_numpy() / (1 + gui1.frame), 512))
        gui2.set_image(ti.imresize(img2.to_numpy() / (1 + gui2.frame), 512))
        gui1.show()
        gui2.show()
