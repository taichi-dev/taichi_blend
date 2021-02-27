'''
common utilities used by this project
'''

import taichi as ti
import numpy as np


hasattr(ti, '_tinahacked') or setattr(ti, '_tinahacked', 1) or setattr(ti,
        'static', lambda x, *xs: [x] + list(xs) if xs else x) or setattr(
        ti.Matrix, 'element_wise_writeback_binary', (lambda f: lambda x, y, z:
        (y.__name__ != 'assign' or not setattr(y, '__name__', '_assign'))
        and f(x, y, z))(ti.Matrix.element_wise_writeback_binary)) or setattr(
        ti.Matrix, 'is_global', (lambda f: lambda x: len(x) and f(x))(
        ti.Matrix.is_global)) or setattr(ti.TaichiOperations, '__pos__',
        lambda x: x) or setattr(ti, 'pi', __import__('math').pi) or setattr(ti,
        'tau', __import__('math').tau) or setattr(ti, 'materialize_callback',
        (lambda f: lambda x: [(x() if ti.get_runtime().materialized else f(x)),
        x][1])(ti.materialize_callback)) or setattr(ti, 'expr_init', (lambda f:
        lambda x: x if isinstance(x, (dict, str)) or x is ti else f(x))(
        ti.expr_init)) or setattr(ti, 'expr_init_func', (lambda f: lambda x: x
        if isinstance (x, (dict, str)) or x is ti else f(x))(ti.expr_init_func)
        ) or print('[Tina] Taichi properties hacked')


eps = 1e-6
inf = 1e6


def V(*xs):
    return ti.Vector(xs)


def V23(xy, z):
    return V(xy.x, xy.y, z)


def V34(xyz, w):
    return V(xyz.x, xyz.y, xyz.z, w)


def V43(v):
    return v.xyz / v.w


def V2(x):
    if isinstance(x, ti.Matrix):
        return x
    else:
        return V(x, x)


def V3(x):
    if isinstance(x, ti.Matrix):
        return x
    else:
        return V(x, x, x)


def V4(x):
    if isinstance(x, ti.Matrix):
        return x
    else:
        return V(x, x, x, x)


def Vavg(u):
    if isinstance(u, ti.Matrix):
        return u.sum() / len(u.entries)
    else:
        return u


def Vall(u):
    if isinstance(u, ti.Matrix):
        return u.all()
    else:
        return u


def Vlen2(u):
    if isinstance(u, ti.Matrix):
        return u.norm_sqr()
    else:
        return u**2


def Vlen(u):
    if isinstance(u, ti.Matrix):
        return u.norm()
    else:
        return u2


def Vany(u):
    if isinstance(u, ti.Matrix):
        return u.any()
    else:
        return u


def U3(i):
    return ti.Vector.unit(3, i)


def U2(i):
    return ti.Vector.unit(2, i)


ti.Matrix.xy = property(lambda v: V(v.x, v.y))
ti.Matrix.xz = property(lambda v: V(v.x, v.z))
ti.Matrix.Yx = property(lambda v: V(-v.y, v.x))
ti.Matrix.xZy = property(lambda v: V(v.x, -v.z, v.y))
ti.Matrix.xyz = property(lambda v: V(v.x, v.y, v.z))


@ti.pyfunc
def Vprod(w):
    v = tovector(w)
    if ti.static(not v.entries):
        return 1
    x = v.entries[0]
    if ti.static(len(v.entries) > 1):
        for y in ti.static(v.entries[1:]):
            x *= y
    return x


def totuple(x):
    if x is None:
        x = []
    if isinstance(x, ti.Matrix):
        x = x.entries
    if isinstance(x, list):
        x = tuple(x)
    if not isinstance(x, tuple):
        x = [x]
    if isinstance(x, tuple) and len(x) and x[0] is None:
        x = []
    return tuple(x)


def tovector(x):
    return ti.Vector(totuple(x))


def vconcat(*xs):
    res = []
    for x in xs:
        if isinstance(x, ti.Matrix):
            res.extend(x.entries)
        else:
            res.append(x)
    return ti.Vector(res)


@ti.pyfunc
def clamp(x, xmin=0, xmax=1):
    return min(xmax, max(xmin, x))


@ti.pyfunc
def ifloor(x):
    return int(ti.floor(x))


@ti.pyfunc
def iceil(x):
    return int(ti.ceil(x))


@ti.func
def dot_or_zero(a, b):
    return max(0.0, a.dot(b))


@ti.func
def bilerp(f: ti.template(), pos):
    p = float(pos)
    I = ifloor(p)
    x = p - I
    y = 1 - x
    return (f[I + V(1, 1)] * x[0] * x[1] +
            f[I + V(1, 0)] * x[0] * y[1] +
            f[I + V(0, 0)] * y[0] * y[1] +
            f[I + V(0, 1)] * y[0] * x[1])


@ti.func
def trilerp(f: ti.template(), pos):
    p = float(pos)
    I = ifloor(p)
    w0 = p - I
    w1 = 1 - w0

    c00 = f[I + V(0,0,0)] * w1.x + f[I + V(1,0,0)] * w0.x
    c01 = f[I + V(0,0,1)] * w1.x + f[I + V(1,0,1)] * w0.x
    c10 = f[I + V(0,1,0)] * w1.x + f[I + V(1,1,0)] * w0.x
    c11 = f[I + V(0,1,1)] * w1.x + f[I + V(1,1,1)] * w0.x

    c0 = c00 * w1.y + c10 * w0.y
    c1 = c01 * w1.y + c11 * w0.y

    return c0 * w1.z + c1 * w0.z


@ti.func
def tanspace(nrm, up=V(233., 666., 512.)):
    bitan = nrm.cross(up).normalized()
    tan = bitan.cross(nrm)
    return ti.Matrix.cols([tan, bitan, nrm])



@ti.func
def spherical(h, p):
    unit = V(ti.cos(p * ti.tau), ti.sin(p * ti.tau))
    dir = V23(ti.sqrt(max(0, 1 - h**2)) * unit, h)
    return dir


@ti.func
def unspherical(dir):
    p = ti.atan2(dir.y, dir.x) / ti.tau
    return dir.z, p % 1


@ti.func
def dir2tex(dir):
    dir = dir.normalized()
    s = ti.atan2(dir.z, dir.x) / ti.pi * 0.5 + 0.5
    t = ti.atan2(dir.y, dir.xz.norm()) / ti.pi + 0.5
    return V(s, t)


@ti.func
def M33(mat):
    return ti.Matrix([[mat[i, j] for j in range(3)] for i in range(3)])


@ti.pyfunc
def reflect(I, N):
    return I - 2 * N.dot(I) * N


@ti.pyfunc
def refract(I, N, eta):
    has_r, T = 0, I * 0
    NoI = N.dot(I)
    discr = 1 - eta**2 * (1 - NoI**2)
    if discr > 0:
        has_r = 1
        T = (eta * I - N * (eta * NoI + ti.sqrt(discr))).normalized()
    return has_r, T


@ti.pyfunc
def smoothstep(x, a, b):
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


@ti.pyfunc
def lerp(fac, src, dst):
    return src * (1 - fac) + dst * fac


@ti.pyfunc
def unlerp(val, src, dst):
    return (val - src) / (dst - src)


@ti.func
def list_subscript(a, i):
    ret = sum(a) * 0
    for j in ti.static(range(len(a))):
        if i == j:
            ret = a[j]
    return ret


@ti.func
def isnan(x):
    return not (x >= 0 or x <= 0)


def ranprint(*args, rate=1e-3):
    @ti.func
    def func(rate):
        if ti.random() < rate:
            print(*args)

    func(rate)


@ti.func
def random2(rng=ti):
    return V(rng.random(), rng.random())


@ti.func
def random3(rng=ti):
    return V(rng.random(), rng.random(), rng.random())


def clamp_unsigned(x):
    def _clamp_unsigned_to_range(npty, val):
        iif = np.iinfo(npty)
        if iif.min <= val <= iif.max:
            return val
        cap = (1 << iif.bits)
        if not (0 <= val < cap):
            return val
        new_val = val - cap
        return new_val

    if ti.inside_kernel():
        if ti.impl.get_runtime().default_ip in {ti.i32, ti.u32}:
            return _clamp_unsigned_to_range(np.int32, x)
        elif ti.impl.get_runtime().default_ip in {ti.i64, ti.u64}:
            return _clamp_unsigned_to_range(np.int64, x)
    return x


@ti.pyfunc
def truth(x):
    return (-1 if x != 0 else 0)


# https://stackoverflow.com/questions/27229371/inverse-error-function-in-c
@ti.pyfunc
def erfinv(x):
    sgn = -1 if x < 0 else 1

    x = (1 - x) * (1 + x)
    lnx = ti.log(x)

    tt1 = 2 / (ti.pi * 0.147) + 0.5 * lnx
    tt2 = 1 / 0.147 * lnx

    return sgn * ti.sqrt(-tt1 + ti.sqrt(tt1**2 - tt2))


@ti.pyfunc
def normaldist(samp):
    return ti.sqrt(2) * erfinv(samp * 2 - 1)


class namespace(dict):
    is_taichi_class = True

    def __init__(self, **kwargs):
        res = dict()
        for k, v in kwargs.items():
            res[k] = ti.expr_init(v)
        super().__init__(res)

    class FakeAssign:
        is_taichi_class = True

        def __init__(self, parent, name):
            self.parent = parent
            self.name = name

        def assign(self, value):
            self.parent[self.name] = ti.expr_init(value)

        def __call__(self, *args, **kwargs):
            raise AttributeError(self.name) from None

        def __getattr__(self, name):
            raise AttributeError(self.name + '.' + name) from None

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            if not ti.inside_kernel():
                raise AttributeError(name) from None
            return self.FakeAssign(self, name)

    def assign(self, other):
        assert list(self.keys()) == list(other.keys())
        for k, v in other.items():
            ti.assign(getattr(self, k), v)

    def variable(self):
        return self


def subscripter(foo):
    import functools

    @functools.wraps(foo)
    def wrapped(self, *indices):
        foo(self, indices)

    return wrapped


class Singleton(type):
    _instance = None

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance


def please_install(name):
    if ti.get_os_name() == 'win':
        pip = 'python3 -m pip'
    else:
        pip = 'python -m pip'
    raise ImportError(f'Please run `{pip} install -U {name}`') from None
