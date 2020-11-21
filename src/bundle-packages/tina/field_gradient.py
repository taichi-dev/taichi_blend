from . import *


@A.register
class Def(IField):
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
        self.meta = A.edit_meta(FMeta(self.src), vdims=self.dim)

    @ti.func
    def _subscript(self, I):
        res = ti.Vector.zero(self.meta.dtype, self.dim)
        for i in ti.static(range(self.dim)):
            D = ti.Vector.unit(self.dim, i)
            res[i] = self.src[I + D] - self.src[I - D]
        return res


