from . import *


@A.register
class ClearBuffer(IField, IRun):
    '''
    Name: clear_buffer
    Category: render
    Inputs: buffer:cf update:t
    Output: buffer:cf update:t
    '''

    def __init__(self, buf, chain):
        super().__init__(chain)

        assert isinstance(buf, IField)

        self.buf = buf
        self.meta = FMeta(buf)

    @ti.func
    def _subscript(self, I):
        return self.buf[I]

    @ti.kernel
    def _run(self):
        for I in ti.static(self.buf):
            self.buf[I] *= 0
