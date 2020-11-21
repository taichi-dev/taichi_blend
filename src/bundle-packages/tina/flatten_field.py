from . import *


@A.register
class Def(IField):
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
