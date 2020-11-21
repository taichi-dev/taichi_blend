from . import *


@A.register
class Def(IField, IRun):
    '''
    Name: double_buffer
    Category: storage
    Inputs: meta:m
    Output: current:f update:t
    '''

    def __init__(self, meta):
        assert isinstance(meta, Meta)

        self.meta = meta
        self.cur = Field(self.meta)
        self.nxt = Field(self.meta)
        self.src = None

    def swap(self):
        self.cur, self.nxt = self.nxt, self.cur

    def run(self):
        assert self.src is not None, 'A.double_buffer must come with A.bind_source'
        self._run(self.nxt, self.src)
        self.swap()

    @ti.kernel
    def _run(self, nxt: ti.template(), src: ti.template()):
        for I in ti.static(nxt):
            nxt[I] = src[I]

    @ti.func
    def _subscript(self, I):
        return self.cur[I]
