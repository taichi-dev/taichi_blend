from . import *


@A.register
class ParticleRasterize(IField, IRun):
    '''
    Name: particle_rasterize
    Category: render
    Inputs: buffer:cf verts:f update:t
    Output: buffer:cf update:t
    '''

    def __init__(self, buf, pos, chain):
        super().__init__(chain)

        assert isinstance(buf, IField)
        assert isinstance(pos, IField)

        self.buf = buf
        self.pos = pos
        self.meta = FMeta(buf)

    @ti.func
    def _subscript(self, I):
        return self.buf[I]

    @ti.kernel
    def _run(self):
        screen = ti.static(V(*self.meta.shape))

        for I in ti.static(self.pos):
            pos = self.pos[I]
            base = int(ti.floor(pos))

            if all(0 <= base < screen):
                self.buf[base] = 1
