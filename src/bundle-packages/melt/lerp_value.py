from . import *


@A.register
class Def(IField):
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


