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
    docs = cls.__doc__.strip().splitlines()

    node_name = None
    inputs = []
    outputs = []
    category = 'uncategorized'
    converter = getattr(cls, 'ns_convert', lambda *x: x)

    for line in docs:
        line = [l.strip() for l in line.split(':', 1)]
        if line[0] == 'Name':
            node_name = line[1].replace(' ', '_')
        if line[0] == 'Inputs':
            inputs = line[1].split()
        if line[0] == 'Output':
            outputs = line[1].split()
        if line[0] == 'Category':
            category = line[1]

    type2socket = {
            'm': 'meta',
            'f': 'field',
            'mf': 'meta_field',
            'vf': 'vector_field',
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
            setattr(Def, f'input_{isoc}', (name, socket))
            isoc += 1

    for i, arg in enumerate(outputs):
        name, type = arg.split(':', 1)
        socket = type2socket[type]
        setattr(Def, f'output_{i + 1}', (name, socket))

    def wrapped(*args):
        args = converter(*args)
        return cls(*args)

    setattr(Def, 'category', category)
    setattr(Def, 'wrapped', wrapped)
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
    '''
    Name: make_meta
    Category: meta
    Inputs: shape:i3 dtype:dt vdims:i2
    Output: meta:m
    '''

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
    '''
    Name: specify_meta
    Category: meta
    Inputs: meta:m field:f
    Output: field:mf
    '''

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
    '''
    Name: imitate_meta
    Category: meta
    Inputs: source:mf field:f
    Output: field:mf
    '''

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
    '''
    Name: cache_field
    Category: storage
    Inputs: source:mf
    Output: cached:mf
    '''

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
    '''
    Name: double_buffer
    Category: storage
    Inputs: source:mf
    Output: current:mf
    '''

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
    '''
    Name: field_storage
    Category: storage
    Inputs: meta:m
    Output: field:mf
    '''

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
    '''
    Name: constant_field
    Category: sampler
    Inputs: value:c
    Output: field:f
    '''

    def __init__(self, value):
        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value


@ns_register
class FUniform(IField):
    '''
    Name: uniform_field
    Category: sampler
    Inputs: value:f
    Output: field:f
    '''

    def __init__(self, value):
        assert isinstance(value, IField)

        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value[None]


@ns_register
class FBound(IShapeField):
    '''
    Name: bound_sample
    Category: sampler
    Inputs: source:mf
    Output: result:mf
    '''

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        return self.src[clamp(I, 0, ti.Vector(self.meta.shape) - 1)]


@ns_register
class FRepeat(IShapeField):
    '''
    Name: repeat_sample
    Category: sampler
    Inputs: source:mf
    Output: result:mf
    '''

    def __init__(self, src):
        assert isinstance(src, IShapeField)

        self.src = src
        self.meta = self.src.meta

    @ti.func
    def _subscript(self, I):
        return self.src[I % ti.Vector(self.meta.shape)]


@ns_register
class FMix(IField):
    '''
    Name: mix_value
    Category: converter
    Inputs: src:f dst:f ksrc:c kdst:c
    Output: result:f
    '''

    def __init__(self, src, dst, ksrc=1, kdst=1):
        assert isinstance(src, IField)
        assert isinstance(dst, IField)

        self.src = src
        self.dst = dst
        self.ksrc = ksrc
        self.kdst = kdst

    @ti.func
    def _subscript(self, I):
        return self.src[I] * self.ksrc + self.dst[I] * self.kdst


@ns_register
class FLerp(IField):
    '''
    Name: lerp_value
    Category: converter
    Inputs: src0:f src1:f fac:f
    Output: result:f
    '''

    def __init__(self, src0, src1, fac):
        assert isinstance(src0, IField)
        assert isinstance(src1, IField)
        assert isinstance(fac, IField)

        self.src0 = src0
        self.src1 = src1
        self.fac = fac

    @ti.func
    def _subscript(self, I):
        k = self.fac[I]
        return self.src1[I] * k + self.src0[I] * (1 - k)


@ns_register
class FClamp(IField):
    '''
    Name: value_clamp
    Category: sampler
    Inputs: source:f min:c max:c
    Output: clamped:f
    '''

    def __init__(self, src, min=0, max=1):
        assert isinstance(src, IField)

        self.src = src
        self.min = min
        self.max = max

    @ti.func
    def _subscript(self, I):
        return clamp(self.src[I], self.min, self.max)


@ns_register
class FRange(IField):
    '''
    Name: map_value
    Category: converter
    Inputs: value:f src0:c src1:c dst0:c dst1:c clamp:b
    Output: result:f
    '''

    def __init__(self, value, src0=0, src1=1, dst0=0, dst1=1, clamp=False):
        assert isinstance(value, IField)

        self.value = value
        self.src0 = src0
        self.src1 = src1
        self.dst0 = dst0
        self.dst1 = dst1
        self.clamp = clamp

    @ti.func
    def _subscript(self, I):
        k = (self.value[I] - self.src0) / (self.src1 - self.src0)
        if ti.static(self.clamp):
            k = clamp(k, 0, 1)
        return self.dst1 * k + self.dst0 * (1 - k)


@ns_register
class FMultiply(IField):
    '''
    Name: multiply_value
    Category: converter
    Inputs: lhs:f rhs:f
    Output: result:f
    '''

    def __init__(self, lhs, rhs):
        assert isinstance(lhs, IField)
        assert isinstance(rhs, IField)

        self.lhs = lhs
        self.rhs = rhs

    @ti.func
    def _subscript(self, I):
        return self.lhs[I] * self.rhs[I]


@ns_register
class FFunc(IField):
    '''
    Name: fieldwise_function
    Category: converter
    Inputs: *args:f
    Output: result:f
    '''

    def __init__(self, func, *args):
        assert all(isinstance(a, IField) for a in args)

        self.func = func
        self.args = args

    @ti.func
    def _subscript(self, I):
        return self.func(*[a[I] for a in self.args])


@ns_register
class FVChan(IField):
    '''
    Name: vector_component
    Category: converter
    Inputs: vector:vf channel:i
    Output: value:f
    '''

    def __init__(self, field, channel):
        assert isinstance(field, IField)

        self.field = field
        self.channel = channel

    @ti.func
    def _subscript(self, I):
        return self.field[I][self.channel]


@ns_register
class FVPack(IField):
    '''
    Name: pack_vector
    Category: converter
    Inputs: *comps:f
    Output: vector:vf
    '''

    def __init__(self, *args):
        assert all(isinstance(a, IField) for a in args)

        self.args = args

    @ti.func
    def _subscript(self, I):
        args = [a[I] for a in self.args]
        return vconcat(*args)


@ns_register
class FIndex(IField):
    '''
    Name: get_field_index
    Category: sampler
    Inputs: 
    Output: index:vf
    '''

    def __init__(self):
        pass

    @ti.func
    def _subscript(self, I):
        return I


@ns_register
class FShuffle(IField):
    '''
    Name: field_shuffle
    Category: sampler
    Inputs: field:f index:vf
    Output: value:f
    '''

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
    '''
    Name: field_bilerp
    Category: sampler
    Inputs: field:f pos:vf
    Output: value:f
    '''

    def __init__(self, field, pos):
        assert isinstance(field, IField)
        assert isinstance(index, IField)

        self.field = field
        self.pos = pos

    @ti.func
    def _subscript(self, I):
        return bilerp(self.field, self.pos[I])


@ns_register
class FVTrans(IField):
    '''
    Name: affine_transformation
    Category: converter
    Inputs: vector:vf matrix:vf offset:vf
    Output: result:vf
    '''

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
    '''
    Name: chessboard_texture
    Category: texture
    Inputs: size:i
    Output: sample:f
    '''

    def __init__(self, size):
        self.size = size

    @ti.func
    def _subscript(self, I):
        return (I // self.size).sum() % 2


@ns_register
class FGaussDist(IField):
    '''
    Name: gaussian_distrubtion
    Category: texture
    Inputs: center:c2 radius:c height:c
    Output: sample:f
    '''

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
    '''
    Name: field_laplacian
    Category: stencil
    Inputs: source:f
    Output: laplace:f
    '''

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
    '''
    Name: field_gradient
    Category: stencil
    Inputs: source:f
    Output: gradient:vf
    '''

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
    '''
    Name: copy_field
    Category: storage
    Inputs: dest:mf source:f
    Output: task:t
    '''

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
    '''
    Name: accumate_field
    Category: storage
    Inputs: dest:mf source:f
    Output: task:t
    '''

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
    '''
    Name: merge_tasks
    Category: scheduler
    Inputs: *tasks:t
    Output: merged:t
    '''

    def __init__(self, *tasks):
        assert all(isinstance(t, IRun) for t in tasks)

        self.tasks = tasks

    def run(self):
        for t in self.tasks:
            t.run()


@ns_register
class RTimes(IRun):
    '''
    Name: repeat_task
    Category: scheduler
    Inputs: task:t times:i
    Output: repeated:t
    '''

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
    '''
    Name: canvas_visualize
    Category: output
    Inputs: image:vf res:i2
    Output:
        '''

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
