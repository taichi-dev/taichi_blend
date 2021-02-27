from . import *


@A.register
class Def(IRun, IField):
    '''
    Name: cache_field
    Category: storage
    Inputs: source:f update:t
    Output: cached:cf update:t
    '''

    def __init__(self, src, chain):
        super().__init__(chain)

        assert isinstance(src, IField)

        self.src = src
        self.meta = self.src.meta
        self.buf = Field(self.meta)

    @ti.kernel
    def _run(self):
        for I in ti.static(self.src):
            self.buf[I] = self.src[I]

    @ti.func
    def _subscript(self, I):
        return self.buf[I]
