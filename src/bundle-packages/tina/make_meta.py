from . import *


@A.register
class Meta(INode):
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

    def __init__(self, shape=None, dtype=None, vdims=None, store=None):
        self.dtype = dtype
        self.shape = totuple(shape) if shape is not None else shape
        self.vdims = totuple(vdims) if vdims is not None else vdims
        self.store = store

    def copy(self, other):
        Meta.__init__(self, other.shape, other.dtype, other.vdims, other.store)

    def __repr__(self):
        dtype = self.dtype
        if hasattr(dtype, 'to_string'):
            dtype = 'ti.' + dtype.to_string()
        elif hasattr(dtype, '__name__'):
            dtype = dtype.__name__
        return f'Meta({list(self.shape)}, {dtype}, {list(self.vdims)})'


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


Def = Meta
