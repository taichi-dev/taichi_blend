from . import *


@A.register
class Field(IField):
    '''
    Name: field_storage
    Category: storage
    Inputs: meta:m
    Output: field:cf
    '''

    def __init__(self, meta):
        assert isinstance(meta, Meta)

        self.meta = MEdit(meta, store=self)
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

    def __getattr__(self, attr):
        return getattr(self.core, attr)

    def __getitem__(self, item):
        return self.core[item]

    def __setitem__(self, item, value):
        self.core[item] = value


Def = Field
