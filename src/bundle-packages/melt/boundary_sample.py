from . import *


@A.register
class Def(IField):
    '''
    Name: boundary_sample
    Category: sampler
    Inputs: source:f default:c
    Output: result:f
    '''

    def __init__(self, src, default=0):
        assert isinstance(src, IField)

        self.src = src
        self.default = default
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        ret = self.src[I] * 0 + self.default
        if all(0 <= I < ti.Vector(self.meta.shape)):
            ret = self.src[I]
        return ret
