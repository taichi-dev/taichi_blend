from . import *


@A.register
class ParticleRasterize(IField, IRunChain):
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
        for I in ti.static(self.pos):
            pos = self.pos[I]
            xy = V(pos[0], pos[1])
            wh = V(*self.buf.meta.shape)

            uv = xy * wh
            base = int(ti.floor(uv))

            if all(0 <= base < wh):
                self.buf[base] = 1


@A.register
class ApplyTransform(IField):
    '''
    Name: apply_transform
    Category: render
    Inputs: verts:f trans:x
    Output: verts:f
    '''

    def __init__(self, pos, mat):
        assert isinstance(pos, IField)
        assert isinstance(mat, IMatrix)

        self.pos = pos
        self.mat = mat
        self.meta = FMeta(self.pos)

    @ti.func
    def _subscript(self, I):
        mat = self.mat.get_matrix()
        pos = self.pos[I]
        res = pos * 0
        for i in ti.static(range(3)):
            res[i] = mat[i, 3]
        for i, j in ti.static(ti.ndrange(3, 3)):
            res[i] += mat[i, j] * pos[j]
        return res
