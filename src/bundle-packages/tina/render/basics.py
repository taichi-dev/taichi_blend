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
        for I in ti.static(self.pos):
            pos = self.pos[I]
            xy = V(pos[0], pos[1])
            wh = V(*self.buf.meta.shape)
            f = min(wh[0], wh[1]) / 2
            c = wh / 2

            uv = xy * f + c
            base = int(ti.floor(uv))

            if all(0 <= base < wh):
                self.buf[base] = 1


@A.register
class TriangleRasterize(IField, IRun):
    '''
    Name: triangle_rasterize
    Category: render
    Inputs: buffer:cf faverts:f update:t
    Output: buffer:cf update:t
    '''

    def __init__(self, buf, faverts, chain):
        super().__init__(chain)

        assert isinstance(buf, IField)
        assert isinstance(pos, IField)

        self.buf = buf
        self.faverts = faverts
        self.meta = FMeta(buf)

    @ti.func
    def _subscript(self, I):
        return self.buf[I]

    @ti.kernel
    def _run(self):
        raise NotImplementedError


@A.register
class FaceVertices(IField):
    '''
    Name: particle_rasterize
    Category: render
    Inputs: verts:f faces:f
    Output: faverts:f
    '''

    def __init__(self, verts, faces):
        super().__init__(chain)

        assert isinstance(verts, IField)
        assert isinstance(faces, IField)

        self.verts = verts
        self.faces = faces
        self.meta = MEdit(FMeta(faces), vdims=None)

    @ti.func
    def _subscript(self, I):
        indices = self.faces[I]
        return tuple(self.verts[i] for i in indices)


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
