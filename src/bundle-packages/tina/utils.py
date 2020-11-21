import taichi as ti


setattr(ti, 'static', lambda x, *xs: [x] + list(xs) if xs else x) or setattr(
        ti.Matrix, 'element_wise_writeback_binary', (lambda f: lambda x, y, z:
        (y.__name__ != 'assign' or not setattr(y, '__name__', '_assign'))
        and f(x, y, z))(ti.Matrix.element_wise_writeback_binary)) or setattr(
        ti.Matrix, 'is_global', (lambda f: lambda x: len(x) and f(x))(
        ti.Matrix.is_global))


def V(*xs):
    return ti.Vector(xs)


def totuple(x):
    if x is None:
        x = []
    if isinstance(x, ti.Matrix):
        x = x.entries
    if isinstance(x, list):
        x = tuple(x)
    if not isinstance(x, tuple):
        x = x,
    if isinstance(x, tuple) and len(x) and x[0] is None:
        x = []
    return x


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


@ti.func
def clamp(x, xmin, xmax):
    return min(xmax, max(xmin, x))


@ti.func
def bilerp(f: ti.template(), pos):
    p = float(pos)
    I = int(ti.floor(p))
    x = p - I
    y = 1 - x
    ti.static_assert(len(f.meta.shape) == 2)
    return (f[I + V(1, 1)] * x[0] * x[1] +
            f[I + V(1, 0)] * x[0] * y[1] +
            f[I + V(0, 0)] * y[0] * y[1] +
            f[I + V(0, 1)] * y[0] * x[1])


def dtype_from_name(name):
    dtypes = 'i8 i16 i32 i64 u8 u16 u32 u64 f32 f64'.split()
    if name in dtypes:
        return getattr(ti, name)
    if name == 'float':
        return float
    if name == 'int':
        return int
    assert False, name
