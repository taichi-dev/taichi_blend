from . import *


@A.register
class Def(IField):
    '''
    Name: repeat_sample
    Category: sampler
    Inputs: source:f
    Output: result:f
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = FMeta(self.src)

    @ti.func
    def _subscript(self, I):
        return self.src[I % ti.Vector(self.meta.shape)]
