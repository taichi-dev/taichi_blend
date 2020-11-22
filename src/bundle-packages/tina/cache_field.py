from . import *


@A.register
class Def(IField, IRun):
    '''
    Name: cache_field
    Category: storage
    Inputs: source:f
    Output: cached:cf update:t
    '''

    def __init__(self, src):
        assert isinstance(src, IField)

        self.src = src
        self.meta = self.src.meta
        self.buf = Field(self.meta)

    @ti.kernel
    def run(self):
        for I in ti.static(self.src):
            self.buf[I] = self.src[I]

    @ti.func
    def _subscript(self, I):
        return self.buf[I]
