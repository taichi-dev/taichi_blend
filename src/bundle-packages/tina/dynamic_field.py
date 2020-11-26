from . import *


@A.register
class DynamicField(Field):
    '''
    Name: dynamic_field
    Category: storage
    Inputs: meta:m
    Output: field:cf
    '''

    def __init__(self, meta):
        super().__init__(meta)
        assert len(meta.shape) == 1
        self.size = Field(C.int[None])

    def __len__(self):
        return self.size[None]

    @ti.func
    def __iter__(self):
        for I in ti.grouped(ti.ndrange(self.size[None])):
            yield I

    def __repr__(self):
        return f'DynamicField({self.meta})'

    def to_numpy(self):
        size = self.size[None]
        shape = tuple(size) + tuple(self.meta.vdims)
        dtype = self.meta.dtype
        if dtype is int:
            dtype = ti.get_runtime().default_ip
        elif dtype is float:
            dtype = ti.get_runtime().default_fp
        dtype = to_numpy_type(dtype)
        arr = np.empty(shape, dtype=dtype)
        self._to_numpy(arr)
        return arr

    def from_numpy(self, arr):
        assert isinstance(arr, np.ndarray), type(arr)
        size = self.size[None] = arr.shape[0]
        shape = tuple(size) + tuple(self.meta.vdims)
        dtype = to_numpy_type(self.meta.dtype)
        assert arr.shape == shape, (arr.shape, shape)
        assert arr.dtype == dtype, (arr.dtype, dtype)
        self._from_numpy(arr)

    def __str__(self):
        return str(self.core)


Def = DynamicField
