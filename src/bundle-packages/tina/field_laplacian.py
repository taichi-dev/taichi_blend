from . import *


@A.register
class Def(IField):
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


