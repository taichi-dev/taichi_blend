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


@eval('lambda x: x()')
class A:
    def __init__(self):
        self.nodes = {}

    def __getattr__(self, name):
        if name not in self.nodes:
            raise AttributeError(f'Cannot find any node matches name `{name}`')
        return self.nodes[name].original

    def register(self, cls):
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

        if node_name in self.nodes:
            raise KeyError(f'Node with name `{node_name}` already registered')

        type2socket = {
                'm': 'meta',
                'f': 'field',
                'of': 'object_field',
                'vf': 'vector_field',
                't': 'task',
                'a': 'any',
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

        if len(inputs):
            name, type = inputs[-1].split(':', 1)
            if name.startswith('*') and name.endswith('s'):
                name = name[1:-1]
                inputs.pop()
                for i in range(2):
                    inputs.append(f'{name}{i}:{type}')

        lut = []
        iopt, isoc = 0, 0
        for i, arg in enumerate(inputs):
            name, type = arg.split(':', 1)
            if type in type2option:
                option = type2option[type]
                lut.append((True, iopt))
                iopt += 1
                setattr(Def, f'option_{iopt}', (name, option))
                if option == 'enum':
                    items = tuple(type2items[type])
                    setattr(Def, f'items_{iopt}', items)
            else:
                socket = type2socket[type]
                lut.append((False, isoc))
                isoc += 1
                setattr(Def, f'input_{isoc}', (name, socket))

        for i, arg in enumerate(outputs):
            name, type = arg.split(':', 1)
            socket = type2socket[type]
            setattr(Def, f'output_{i + 1}', (name, socket))

        def wrapped(self, inputs, options):
            # print('+++', inputs, options)
            args = []
            for isopt, index in lut:
                if isopt:
                    args.append(options[index])
                else:
                    args.append(inputs[index])
            # print('===', cls, args)
            args = converter(*args)
            return cls(*args)

        setattr(Def, 'category', category)
        setattr(Def, 'wrapped', wrapped)
        setattr(Def, 'original', cls)
        self.nodes[node_name] = Def

        return cls


@A.register
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

    def __init__(self, shape=None, dtype=None, vdims=None):
        self.dtype = dtype
        self.shape = totuple(shape) if shape is not None else shape
        self.vdims = totuple(vdims) if vdims is not None else vdims

    def copy(self, other):
        Meta.__init__(self, other.shape, other.dtype, other.vdims)

    def __repr__(self):
        dtype = self.dtype
        if hasattr(dtype, 'to_string'):
            dtype = 'ti.' + dtype.to_string()
        elif hasattr(dtype, '__name__'):
            dtype = dtype.__name__
        return f'Meta({list(self.shape)}, {dtype}, {list(self.vdims)})'


@A.register
class MEdit(Meta):
    '''
    Name: edit_meta
    Category: meta
    Inputs: meta:m shape:i3 dtype:dt vdims:i2 eshape:b edtype:b evdims:b
    Output: meta:m
    '''

    def ns_convert(meta, shape, dtype, vdims, eshape, edtype, evdims):
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
        return meta, shape, dtype, vdims, eshape, edtype, evdims

    def __init__(self, meta, shape=None, dtype=None, vdims=None,
            eshape=None, edtype=None, evdims=None):
        if eshape is None:
            eshape = shape is not None
        if edtype is None:
            edtype = dtype is not None
        if evdims is None:
            evdims = vdims is not None

        super().copy(meta)
        if edtype:
            self.dtype = dtype
        if eshape:
            self.shape = totuple(shape)
        if evdims:
            self.vdims = totuple(vdims)


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


@ti.data_oriented
class IRun:
    @ti.kernel
    def run(self):
        raise NotImplementedError


@ti.data_oriented
class IField:
    is_taichi_class = True

    meta = Meta()

    @ti.func
    def _subscript(self, I):
        raise NotImplementedError

    def subscript(self, *indices):
        I = tovector(indices)
        return self._subscript(I)

    @ti.func
    def __iter__(self):
        for I in ti.grouped(ti.ndrange(*self.meta.shape)):
            yield I


@A.register
class FSpec(IField):
    '''
    Name: specify_meta
    Category: meta
    Inputs: meta:m field:f
    Output: field:f
    '''

    def __init__(self, meta, field):
        assert isinstance(meta, Meta)
        assert isinstance(field, IField)

        self.meta = meta
        self.field = field

    @ti.func
    def _subscript(self, I):
        return self.field[I]


@A.register
def FMeta(field):
    '''
    Name: get_meta
    Category: meta
    Inputs: field:f
    Output: meta:m
    '''
    assert isinstance(field, IField)

    return field.meta


@A.register
class FCache(IField, IRun):
    '''
    Name: cache_field
    Category: storage
    Inputs: source:f
    Output: cached:f update:t
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

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


@A.register
class FDouble(IField, IRun):
    '''
    Name: double_buffer
    Category: storage
    Inputs: meta:m
    Output: current:f double:f update:t
    '''

    def __init__(self, meta):
        assert isinstance(meta, Meta)

        self.meta = meta
        self.cur = Field(self.meta)
        self.nxt = Field(self.meta)
        self.src = None

    def swap(self):
        self.cur, self.nxt = self.nxt, self.cur

    def run(self):
        assert self.src is not None, 'FDouble must come with FDBind'
        self._run(self.nxt, self.src)
        self.swap()

    @ti.kernel
    def _run(self, nxt: ti.template(), src: ti.template()):
        for I in ti.static(nxt):
            nxt[I] = src[I]

    @ti.func
    def _subscript(self, I):
        return self.cur[I]


@A.register
def FDBind(buf, src):
    '''
    Name: bind_source
    Category: storage
    Inputs: double:f source:f
    Output:
    '''
    assert isinstance(buf, FDouble)
    assert isinstance(src, IField)

    buf.src = src


@A.register
class Field(IField):
    '''
    Name: field_storage
    Category: storage
    Inputs: meta:m
    Output: field:f
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

    def __getitem__(self, item):
        return self.core[item]

    def __setitem__(self, item, value):
        self.core[item] = value


@A.register
class FConst(IField):
    '''
    Name: constant_field
    Category: parameter
    Inputs: value:c
    Output: field:f
    '''

    def __init__(self, value):
        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value


@A.register
class FUniform(IField):
    '''
    Name: uniform_field
    Category: parameter
    Inputs: value:f
    Output: field:f
    '''

    def __init__(self, value):
        assert isinstance(value, IField)

        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value[None]


@A.register
class FFlatten(IField):
    '''
    Name: flatten_field
    Category: sampler
    Inputs: source:f
    Output: result:f
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = FMeta(src)
        self.dim = len(self.meta.shape)

        size = 1
        for i in range(self.dim):
            size *= self.meta.shape[i]

        self.meta = MEdit(self.meta, shape=size)

    @ti.func
    def _subscript(self, I):
        ti.static_assert(I.n == 1)
        index = I[0]

        J = ti.Vector.zero(int, self.dim)
        for i in ti.static(range(self.dim)):
            axis = self.src.meta.shape[i]
            J[i] = index % axis
            index //= axis

        return self.src[J]


@A.register
class FBound(IField):
    '''
    Name: bound_sample
    Category: sampler
    Inputs: source:f
    Output: result:f
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        return self.src[clamp(I, 0, ti.Vector(self.meta.shape) - 1)]


@A.register
class FRepeat(IField):
    '''
    Name: repeat_sample
    Category: sampler
    Inputs: source:f
    Output: result:f
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        return self.src[I % ti.Vector(self.meta.shape)]


@A.register
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
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        return self.src[I] * self.ksrc + self.dst[I] * self.kdst


@A.register
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
        self.meta = FMeta(self.fac)

    @ti.func
    def _subscript(self, I):
        k = self.fac[I]
        return self.src1[I] * k + self.src0[I] * (1 - k)


@A.register
class FClamp(IField):
    '''
    Name: clamp_value
    Category: converter
    Inputs: source:f min:c max:c
    Output: clamped:f
    '''

    def __init__(self, src, min=0, max=1):
        assert isinstance(src, IField)

        self.src = src
        self.min = min
        self.max = max
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        return clamp(self.src[I], self.min, self.max)


@A.register
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
        self.meta = FMeta(self.value)

    @ti.func
    def _subscript(self, I):
        k = (self.value[I] - self.src0) / (self.src1 - self.src0)
        if ti.static(self.clamp):
            k = clamp(k, 0, 1)
        return self.dst1 * k + self.dst0 * (1 - k)


@A.register
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
        self.meta = FMeta(self.lhs)

    @ti.func
    def _subscript(self, I):
        return self.lhs[I] * self.rhs[I]


@A.register
class FFunc(IField):
    '''
    Name: apply_function
    Category: converter
    Inputs: func:s *args:f
    Output: result:f
    '''

    def ns_convert(func, *args):
        for name in 'print min max int float any all'.split():
            func = func.replace(name, 'ti.ti_' + name)
        func = eval(f'lambda x, y: ({func})')
        return func, *args

    def __init__(self, func, *args):
        assert all(isinstance(a, IField) for a in args)

        self.func = func
        self.args = args
        if len(self.args):
            self.meta = FMeta(self.args[0])

    @ti.func
    def _subscript(self, I):
        return self.func(*[a[I] for a in self.args])


@A.register
class FVChannel(IField):
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
        self.meta = MEdit(FMeta(self.field), vdims=())

    @ti.func
    def _subscript(self, I):
        return self.field[I][self.channel]


@A.register
class FVLength(IField):
    '''
    Name: vector_length
    Category: converter
    Inputs: vector:vf
    Output: length:f
    '''

    def __init__(self, field):
        assert isinstance(field, IField)

        self.field = field
        self.meta = MEdit(FMeta(self.field), vdims=())

    @ti.func
    def _subscript(self, I):
        return self.field[I].norm()


@A.register
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
        if len(self.args):
            self.meta = FMeta(self.args[0])

    @ti.func
    def _subscript(self, I):
        args = [a[I] for a in self.args]
        return vconcat(*args)


@A.register
class FIndex(IField):
    '''
    Name: field_index
    Category: parameter
    Inputs:
    Output: index:vf
    '''

    def __init__(self):
        pass

    @ti.func
    def _subscript(self, I):
        return I


@A.register
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
        self.meta = FMeta(self.index)

    @ti.func
    def _subscript(self, I):
        return self.field[self.index[I]]


@A.register
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
        self.meta = FMeta(self.pos)

    @ti.func
    def _subscript(self, I):
        return bilerp(self.field, self.pos[I])


@A.register
class FVTrans(IField):
    '''
    Name: affine_transform
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
        self.meta = FMeta(self.vec)

    @ti.func
    def _subscript(self, I):
        return self.mat[I] @ self.vec[I] + self.off[I]


@A.register
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


@A.register
class FRandom(IField):
    '''
    Name: random_generator
    Category: texture
    Inputs:
    Output: sample:f
    '''

    def __init__(self):
        pass

    @ti.func
    def _subscript(self, I):
        return ti.random()


@A.register
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


@A.register
class FLaplacian(IField):
    '''
    Name: field_laplacian
    Category: stencil
    Inputs: source:f
    Output: laplace:f
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        dim = ti.static(len(self.meta.shape))
        res = -2 * dim * self.src[I]
        for i in ti.static(range(dim)):
            D = ti.Vector.unit(dim, i)
            res += self.src[I + D] + self.src[I - D]
        return res / (2 * dim)


@A.register
class FGradient(IField):
    '''
    Name: field_gradient
    Category: stencil
    Inputs: source:f
    Output: gradient:vf
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.dim = len(self.src.meta.shape)
        self.meta = MEdit(FMeta(self.src), vdims=self.dim)

    @ti.func
    def _subscript(self, I):
        res = ti.Vector.zero(self.meta.dtype, self.dim)
        for i in ti.static(range(self.dim)):
            D = ti.Vector.unit(self.dim, i)
            res[i] = self.src[I + D] - self.src[I - D]
        return res


@A.register
class RFCopy(IRun):
    '''
    Name: copy_field
    Category: task
    Inputs: dest:f source:f
    Output: task:t
    '''

    def __init__(self, dst, src):
        assert isinstance(dst, IField)
        assert isinstance(src, IField)

        self.dst = dst
        self.src = src

    @ti.kernel
    def run(self):
        for I in ti.static(self.dst):
            self.dst[I] = self.src[I]


@A.register
class RFAccumate(IRun):
    '''
    Name: accumate_field
    Category: task
    Inputs: dest:f source:f
    Output: task:t
    '''

    def __init__(self, dst, src):
        assert isinstance(dst, IField)
        assert isinstance(src, IField)

        self.dst = dst
        self.src = src

    @ti.kernel
    def run(self):
        for I in ti.static(self.dst):
            self.dst[I] += self.src[I]


@A.register
class RMerge(IRun):
    '''
    Name: merge_tasks
    Category: task
    Inputs: *tasks:t
    Output: merged:t
    '''

    def __init__(self, *tasks):
        assert all(isinstance(t, IRun) for t in tasks)

        self.tasks = tasks

    def run(self):
        for t in self.tasks:
            t.run()


@A.register
class RTimes(IRun):
    '''
    Name: repeat_task
    Category: task
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


@A.register
class RNull(IRun):
    '''
    Name: null_task
    Category: task
    Inputs:
    Output: task:t
    '''

    def __init__(self):
        pass

    def run(self):
        pass


@A.register
class RCanvas(IRun):
    '''
    Name: canvas_visualize
    Category: output
    Inputs: image:vf update:t res:i2
    Output: task:t
    '''

    def __init__(self, img, update, res=None):
        assert isinstance(img, IField)
        assert isinstance(update, IRun)

        self.img = img
        self.update = update
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

    def run(self):
        gui = ti.GUI(res=self.res, fast_gui=True)
        while gui.running:
            gui.get_event(None)
            gui.running = not gui.is_pressed(gui.ESCAPE)
            self.update.run()
            self.render(gui.img, gui.res)
            gui.show()


@A.register
class RStaticPrint(IRun):
    '''
    Name: static_print
    Category: output
    Inputs: value:a
    Output: task:t
    '''

    def __init__(self, value):
        self.value = value

    def run(self):
        print(self.value)


@A.register
def FLaplacianBlur(x):
    '''
    Name: laplacian_blur
    Category: stencil
    Inputs: source:f
    Output: result:f
    '''
    return FMix(x, FLaplacian(FBound(x)), 1, 1)


@A.register
def FLaplacianStep(pos, vel, kappa):
    '''
    Name: laplacian_step
    Category: physics
    Inputs: pos:f vel:f kappa:c
    Output: vel:f
    '''
    return FMix(vel, FLaplacian(FBound(pos)), 1, kappa)


@A.register
def FPosAdvect(pos, vel, dt):
    '''
    Name: advect_position
    Category: physics
    Inputs: pos:f vel:f dt:c
    Output: pos:f
    '''
    return FMix(pos, vel, 1, dt)


if __name__ == '__main__':
    ini = FSpec(C.float[512, 512], FGaussDist([256, 256], 6, 8))
    pos = FDouble(FMeta(ini))
    vel = FDouble(FMeta(ini))
    FDBind(pos, FPosAdvect(pos, vel, 0.1))
    FDBind(vel, FLaplacianStep(pos, vel, 1))
    init = RMerge(RFCopy(pos, ini), RFCopy(vel, FConst(0)))
    step = RTimes(RMerge(pos, vel), 8)
    vis = FMix(FVPack(pos, FGradient(pos)), FConst(1), 0.5, 0.5)
    init.run()
    gui = RCanvas(vis, step)
    gui.run()


__all__ = ['ti', 'A', 'C', 'IRun', 'IField', 'Meta', 'Field',
           'clamp', 'bilerp', 'totuple', 'tovector', 'V']
