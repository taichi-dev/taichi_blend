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


ns_nodes = {}

def ns_register(cls):
    node_name = cls.ns_name.replace(' ', '_')
    inputs = cls.ns_inputs.split()
    outputs = cls.ns_output.split()
    category = getattr(cls, 'ns_category', 'default')
    converter = getattr(cls, 'ns_convert', lambda *x: x)

    type2socket = {
            'm': 'meta',
            'f': 'field',
            't': 'task',
    }
    type2option = {
            'dt': 'enum',
            'i': 'int',
            'c': 'float',
            'b': 'bool',
            's': 'str',
            'so': 'search_object',
            'i2': 'vec_int_2',
            'i3': 'vec_int_3',
            'c2': 'vec_float_2',
            'c3': 'vec_float_3',
    }
    type2items = {
            'dt': 'float int i8 i16 i32 i64 u8 u16 u32 u64 f32 f64'.split(),
    }

    class Def:
        pass

    iopt, isoc = 1, 1
    for i, arg in enumerate(inputs):
        name, type = arg.split(':', 1)
        if type in type2option:
            option = type2option[type]
            setattr(Def, f'option_{iopt}', (name, option))
            if option == 'enum':
                items = tuple(type2items[type])
                setattr(Def, f'items_{iopt}', items)
            iopt += 1
        else:
            socket = type2socket[type]
            setattr(Def, f'input_{iopt}', (name, socket))
            isoc += 1

    for i, arg in enumerate(outputs):
        name, type = arg.split(':', 1)
        socket = type2socket[type]
        setattr(Def, f'output_{i + 1}', (name, socket))

    setattr(Def, 'category', category)
    ns_nodes[node_name] = Def
    return cls


@ti.data_oriented
class IField:
    is_taichi_class = True

    @ti.func
    def _subscript(self, I):
        raise NotImplementedError

    def subscript(self, *indices):
        I = tovector(indices)
        return self._subscript(I)

    @ti.func
    def __iter__(self):
        raise NotImplementedError


@ns_register
@ti.data_oriented
class Meta:
    ns_name = 'make_meta'
    ns_inputs = 'shape:i3 dtype:dt vdims:i2'
    ns_output = 'meta:m'

    def ns_convert(shape, dtype, vdims):
        dtype = dtype_from_name(dtype)
        if shape[2] == 0:
            shape = shape[0], shape[1]
        if shape[1] == 0:
            shape = shape[0],
        if shape[0] == 0:
            shape = ()
        if vdims[1] == 0:
            vdims = vdims[0],
        if vdims[0] == 0:
            vdims = ()
        return shape, dtype, vdims

    is_taichi_class = True

    def __init__(self, shape, dtype=None, vdims=None):
        self.dtype = dtype
        self.shape = totuple(shape)
        self.vdims = totuple(vdims)

    @classmethod
    def copy(cls, other):
        return cls(other.shape, other.dtype, other.vdims)

    def __repr__(self):
        dtype = self.dtype
        if hasattr(dtype, 'to_string'):
            dtype = 'ti.' + dtype.to_string()
        elif hasattr(dtype, '__name__'):
            dtype = dtype.__name__
        return f'Meta({dtype}, {list(self.vdims)}, {list(self.shape)})'


@eval('lambda x: x()')
class C:
    class _TVS(Meta):
        def __init__(self, dtype, dt_name, vdims, vd_name, shape, sh_name):
            self.dt_name = dt_name
            self.vd_name = vd_name
            self.sh_name = sh_name
            super().__init__(shape, dtype, vdims)

        def __repr__(self):
            return f'C.{self.dt_name}{self.vd_name}[{self.sh_name}]'

    class _TV(Meta):
        def __init__(self, dtype, dt_name, vdims, vd_name):
            self.dt_name = dt_name
            self.vd_name = vd_name
            super().__init__(None, dtype, vdims)

        def __getitem__(self, indices):
            shape = totuple(indices)
            sh_name = repr(indices)
            if sh_name.startswith('(') and sh_name.endswith(')'):
                sh_name = sh_name[1:-1]
                if sh_name.endswith(','):
                    sh_name = sh_name[-1]

            return C._TVS(self.dtype, self.dt_name,
                    self.vdims, self.vd_name, shape, sh_name)

        def __repr__(self):
            return f'C.{self.dt_name}{self.vd_name}'

    class _T(Meta):
        def __init__(self, dtype, dt_name):
            self.dt_name = dt_name
            super().__init__(None, dtype, None)

        def __getitem__(self, indices):
            return C._TV(self.dtype, self.dt_name, (), '')[indices]

        def __call__(self, *indices):
            vdims = totuple(indices)
            vd_name = repr(indices)
            if vd_name.startswith('(') and vd_name.endswith(')'):
                vd_name = vd_name[1:-1]
                if vd_name.endswith(','):
                    vd_name = vd_name[:-1]

            return C._TV(self.dtype, self.dt_name, vdims, f'({vd_name})')

        def __repr__(self):
            return f'C.{self.dt_name}'

    def __getattr__(self, name):
        dtype = dtype_from_name(name)
        return C._T(dtype, name)

    def __repr__(self):
        return 'C'


class IShapeField(IField):
    meta = NotImplemented

    @ti.func
    def __iter__(self):
        for I in ti.grouped(ti.ndrange(*self.meta.shape)):
            yield I


@ti.data_oriented
class IRun:
    @ti.kernel
    def run(self):
        raise NotImplementedError


@ns_register
class FShape(IShapeField):
    ns_name = 'specify_meta'
    ns_inputs = 'meta:m field:f'
    ns_output = 'field:f'

    def __init__(self, meta, field):
        assert isinstance(meta, Meta)
        assert isinstance(field, IField)

        self.meta = meta
        self.field = field

    @ti.func
    def _subscript(self, I):
        return self.field[I]


@ns_register
class FLike(IShapeField):
    ns_name = 'imitate_meta'
    ns_inputs = 'source:f field:f'
    ns_output = 'field:f'

    def __init__(self, src, field):
        assert isinstance(src, IShapeField)
        assert isinstance(field, IField)

        self.field = field
        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        return self.field[I]


@ns_register
class FCache(IShapeField, IRun):
    ns_name = 'cache_field'
    ns_inputs = 'source:f'
    ns_output = 'cached:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta
        self.buf = Field(self.meta)

    @ti.kernel
    def run(self):
        for I in ti.static(self.src):
            self.buf[I] = self.src[I]

    @ti.func
    def _subscript(self, I):
        return self.buf[I]


@ns_register
class FDouble(IShapeField, IRun):
    ns_name = 'double_buffer'
    ns_inputs = 'source:f'
    ns_output = 'current:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta
        self.cur = Field(self.meta)
        self.nxt = Field(self.meta)

    def swap(self):
        self.cur, self.nxt = self.nxt, self.cur

    def run(self):
        self._run(self.nxt, self.src)
        self.swap()

    @ti.kernel
    def _run(self, nxt: ti.template(), src: ti.template()):
        for I in ti.static(src):
            nxt[I] = src[I]

    @ti.func
    def _subscript(self, I):
        return self.cur[I]


@ns_register
class Field(IShapeField):
    ns_name = 'field_storage'
    ns_inputs = 'meta:m'
    ns_output = 'field:f'

    def __init__(self, meta):
        assert isinstance(meta, Meta)

        self.meta = meta
        self.core = self.__mkfield(meta.dtype, meta.vdims, meta.shape)

    @staticmethod
    def __mkfield(dtype, vdims, shape):
        if len(vdims) == 0:
            return ti.field(dtype, shape)
        elif len(vdims) == 1:
            return ti.Vector.field(vdims[0], dtype, shape)
        elif len(vdims) == 2:
            return ti.Matrix.field(vdims[0], vdims[1], dtype, shape)
        else:
            assert False, vdims

    def subscript(self, *indices):
        return ti.subscript(self.core, *indices)

    @ti.func
    def __iter__(self):
        for I in ti.grouped(self.core):
            yield I

    def __repr__(self):
        return f'Field({self.meta})'

    def __str__(self):
        return str(self.core)

    def __getattr__(self, attr):
        return getattr(self.core, attr)


@ns_register
class FConst(IField):
    ns_name = 'constant_field'
    ns_inputs = 'value:c'
    ns_output = 'field:f'

    def __init__(self, value):
        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value


@ns_register
class FUniform(IField):
    ns_name = 'uniform_field'
    ns_inputs = 'value:f'
    ns_output = 'field:f'

    def __init__(self, value):
        assert isinstance(value, IField)

        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value[None]


@ns_register
class FClamp(IField):
    ns_name = 'clamp_to_range'
    ns_inputs = 'source:f minimum:c maximum:c'
    ns_output = 'clamped:f'

    def __init__(self, src, min=0, max=1):
        assert isinstance(src, IField)

        self.src = src
        self.min = min
        self.max = max

    @ti.func
    def _subscript(self, I):
        return clamp(self.src[I], self.min, self.max)


@ns_register
class FBound(IShapeField):
    ns_name = 'bound_sample'
    ns_inputs = 'source:f'
    ns_output = 'result:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        return self.src[clamp(I, 0, ti.Vector(self.meta.shape) - 1)]


@ns_register
class FRepeat(IShapeField):
    ns_name = 'repeat_sample'
    ns_inputs = 'source:f'
    ns_output = 'result:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        return self.src[I % ti.Vector(self.meta.shape)]


@ns_register
class FMix(IField):
    ns_name = 'mix_value'
    ns_inputs = 'f1:f f2:f k1:c k2:c'
    ns_output = 'result:f'

    def __init__(self, f1, f2, k1=1, k2=1):
        assert isinstance(f1, IField)
        assert isinstance(f2, IField)

        self.f1 = f1
        self.f2 = f2
        self.k1 = k1
        self.k2 = k2

    @ti.func
    def _subscript(self, I):
        return self.f1[I] * self.k1 + self.f2[I] * self.k2


@ns_register
class FMult(IField):
    ns_name = 'multiply_value'
    ns_inputs = 'f1:f f2:f'
    ns_output = 'result:f'

    def __init__(self, f1, f2):
        assert isinstance(f1, IField)
        assert isinstance(f2, IField)

        self.f1 = f1
        self.f2 = f2

    @ti.func
    def _subscript(self, I):
        return self.f1[I] * self.f2[I]


@ns_register
class FFunc(IField):
    ns_name = 'fieldwise_function'
    ns_inputs = '*args:f'
    ns_output = 'result:f'

    def __init__(self, func, *args):
        assert all(isinstance(a, IField) for a in args)

        self.func = func
        self.args = args

    @ti.func
    def _subscript(self, I):
        return self.func(*[a[I] for a in self.args])


@ns_register
class FVChan(IField):
    ns_name = 'vector_component'
    ns_inputs = 'vector:f channel:i'
    ns_output = 'value:f'

    def __init__(self, field, channel):
        assert isinstance(field, IField)

        self.field = field
        self.channel = channel

    @ti.func
    def _subscript(self, I):
        return self.field[I][self.channel]


@ns_register
class FVPack(IField):
    ns_name = 'pack_vector'
    ns_inputs = '*comps:f'
    ns_output = 'vector:f'

    def __init__(self, *args):
        assert all(isinstance(a, IField) for a in args)

        self.args = args

    @ti.func
    def _subscript(self, I):
        args = [a[I] for a in self.args]
        return vconcat(*args)


@ns_register
class FIndex(IField):
    ns_name = 'get_field_index'
    ns_inputs = ''
    ns_output = 'index:f'

    def __init__(self):
        pass

    @ti.func
    def _subscript(self, I):
        return I


@ns_register
class FShuffle(IField):
    ns_name = 'field_shuffle'
    ns_inputs = 'field:f index:f'
    ns_output = 'value:f'

    def __init__(self, field, index):
        assert isinstance(field, IField)
        assert isinstance(index, IField)

        self.field = field
        self.index = index

    @ti.func
    def _subscript(self, I):
        return self.field[self.index[I]]


@ns_register
class FBilerp(IField):
    ns_name = 'field_bilerp'
    ns_inputs = 'field:f index:f'
    ns_output = 'value:f'

    def __init__(self, field, index):
        assert isinstance(field, IField)
        assert isinstance(index, IField)

        self.field = field
        self.index = index

    @ti.func
    def _subscript(self, I):
        return bilerp(self.field, self.index[I])


@ns_register
class FVTrans(IField):
    ns_name = 'affine_transformation'
    ns_inputs = 'vector:f matrix:f offset:f'
    ns_output = 'result:f'

    def __init__(self, vec, mat, off):
        assert isinstance(vec, IField)
        assert isinstance(mat, IField)
        assert isinstance(off, IField)

        self.vec = vec
        self.mat = mat
        self.off = off

    @ti.func
    def _subscript(self, I):
        return self.mat[I] @ self.vec[I] + self.off[I]


@ns_register
class FChessboard(IField):
    ns_name = 'chessboard_texture'
    ns_inputs = 'size:i'
    ns_output = 'sample:f'

    def __init__(self, size):
        self.size = size

    @ti.func
    def _subscript(self, I):
        return (I // self.size).sum() % 2


@ns_register
class FGaussDist(IField):
    ns_name = 'gaussian_distrubtion'
    ns_inputs = 'center:c2 radius:c height:c'
    ns_output = 'sample:f'

    def __init__(self, center, radius, height=1):
        self.center = tovector(center)
        self.radius = radius
        self.height = height

    @ti.func
    def _subscript(self, I):
        r2 = (I - self.center).norm_sqr() / self.radius**2
        return self.height * ti.exp(-r2)


@ns_register
class FLaplacian(IShapeField):
    ns_name = 'field_laplacian'
    ns_inputs = 'source:f'
    ns_output = 'laplace:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        dim = ti.static(len(self.meta.shape))
        res = -2 * dim * self.src[I]
        for i in ti.static(range(dim)):
            D = ti.Vector.unit(dim, i)
            res += self.src[I + D] + self.src[I - D]
        return res / (2 * dim)


@ns_register
class FGradient(IShapeField):
    ns_name = 'field_gradient'
    ns_inputs = 'source:f'
    ns_output = 'gradient:f'

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        dim = ti.static(len(self.meta.shape))
        res = ti.Vector.zero(self.meta.dtype, dim)
        for i in ti.static(range(dim)):
            D = ti.Vector.unit(dim, i)
            res[i] = self.src[I + D] - self.src[I - D]
        return res


@ns_register
class RFCopy(IRun):
    ns_name = 'copy_field'
    ns_inputs = 'dest:f source:f'
    ns_output = 'task:t'

    def __init__(self, dst, src):
        assert isinstance(dst, IShapeField)
        assert isinstance(src, IField)

        self.dst = dst
        self.src = src

    @ti.kernel
    def run(self):
        for I in ti.static(self.dst):
            self.dst[I] = self.src[I]


@ns_register
class RFAccumate(IRun):
    ns_name = 'accumate_field'
    ns_inputs = 'dest:f source:f'
    ns_output = 'task:t'

    def __init__(self, dst, src):
        assert isinstance(dst, IShapeField)
        assert isinstance(src, IField)

        self.dst = dst
        self.src = src

    @ti.kernel
    def run(self):
        for I in ti.static(self.dst):
            self.dst[I] += self.src[I]


@ns_register
class RMerge(IRun):
    ns_name = 'merge_tasks'
    ns_inputs = '*tasks:t'
    ns_output = 'merged:t'

    def __init__(self, *tasks):
        assert all(isinstance(t, IRun) for t in tasks)

        self.tasks = tasks

    def run(self):
        for t in self.tasks:
            t.run()


@ns_register
class RTimes(IRun):
    ns_name = 'repeat_task'
    ns_inputs = 'task:t times:i'
    ns_output = 'repeated:t'

    def __init__(self, task, times):
        assert isinstance(task, IRun)

        self.task = task
        self.times = times

    def run(self):
        for i in range(self.times):
            self.task.run()


@ns_register
@ti.data_oriented
class Canvas:
    ns_name = 'canvas_visualize'
    ns_inputs = 'image:f resolution:i2'
    ns_output = ''

    def __init__(self, img, res=None):
        assert isinstance(img, IShapeField)

        self.img = img
        self.res = res or (512, 512)

    def _cook(self, color):
        if isinstance(color, ti.Expr):
            color = ti.Vector([color, color, color])
        elif isinstance(color, ti.Matrix):
            assert color.m == 1, color.m
            if color.n == 1:
                color = ti.Vector([color(0), color(0), color(0)])
            elif color.n == 2:
                color = ti.Vector([color(0), color(1), 0])
            elif color.n in [3, 4]:
                color = ti.Vector([color(0), color(1), color(2)])
            else:
                assert False, color.n
        if self.img.meta.dtype not in [ti.u8, ti.i8]:
            color = ti.max(0, ti.min(255, ti.cast(color * 255 + 0.5, int)))
        return color

    @ti.func
    def image_at(self, i, j):
        ti.static_assert(len(self.img.meta.shape) == 2)
        scale = ti.Vector(self.img.meta.shape) / ti.Vector(self.res)
        pos = ti.Vector([i, j]) * scale
        r, g, b = self._cook(bilerp(self.img, pos))
        return int(r), int(g), int(b)

    @ti.kernel
    def render(self, out: ti.ext_arr(), res: ti.template()):
        for i in range(res[0] * res[1]):
            r, g, b = self.image_at(i % res[0], res[1] - 1 - i // res[0])
            if ti.static(ti.get_os_name() != 'osx'):
                out[i] = (r << 16) + (g << 8) + b
            else:
                alpha = -16777216
                out[i] = (b << 16) + (g << 8) + r + alpha

    def __iter__(self):
        gui = ti.GUI(res=self.res, fast_gui=True)
        while gui.running:
            gui.get_event(None)
            gui.running = not gui.is_pressed(gui.ESCAPE)
            yield gui
            self.render(gui.img, gui.res)
            gui.show()


def FLaplacianBlur(x):
    return FLike(x, FMix(x, FLaplacian(FBound(x)), 1, 1))


def FLaplacianStep(pos, vel, kappa):
    return FLike(pos, FMix(vel, FLaplacian(FBound(pos)), 1, kappa))


def FPosAdvect(pos, vel, dt):
    return FLike(pos, FMix(pos, vel, 1, dt))


if __name__ == '__main__':
    ini = FShape(C.float[512, 512], FGaussDist([256, 256], 6, 8))
    pos = FDouble(ini)
    vel = FDouble(ini)
    pos.src = FPosAdvect(pos, vel, 0.1)
    vel.src = FLaplacianStep(pos, vel, 1)
    init = RMerge(RFCopy(pos, ini), RFCopy(vel, FConst(0)))
    step = RTimes(RMerge(pos, vel), 8)
    vis = FShape(C.float(3)[512, 512], FMix(FVPack(pos, FGradient(pos)), FConst(1), 0.5, 0.5))
#frm = Field(C.int[None])
#off = FCache(FShape(C.float[None], FFunc(lambda x: 10 * ti.sin(0.1 * x), frm)))
#vis = FCache(FLike(vis, FBilerp(FRepeat(vis), FMix(FIndex(), FUniform(off), 1, 1))))
#step = RMerge(off, vis, step)

    init.run()
    for gui in Canvas(vis):
        #frm.core[None] = gui.frame
        step.run()
