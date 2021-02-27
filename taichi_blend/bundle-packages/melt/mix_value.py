from . import *


@A.register
class Def(IField):
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
