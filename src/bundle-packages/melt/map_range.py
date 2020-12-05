from . import *


@A.register
class Def(IField):
    '''
    Name: map_range
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
