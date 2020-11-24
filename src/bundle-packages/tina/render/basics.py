from . import *


@A.register
class ViewportTransform(IField):
    '''
    Name: viewport_transform
    Category: render
    Inputs: verts:f screen:m
    Output: verts:f
    '''

    def __init__(self, pos, screen):
        if isinstance(screen, IField):
            screen = FMeta(screen)  # auto cast..

        assert isinstance(pos, IField)
        assert isinstance(screen, Meta)

        self.pos = pos
        self.screen = screen
        self.meta = FMeta(pos)

    @ti.func
    def _subscript(self, I):
        pos = self.pos[I]
        xy = V(pos[0], pos[1])
        wh = V(*self.screen.shape)
        fg = min(wh[0], wh[1]) / 2
        cd = wh / 2
        uv = xy * fg + cd
        return uv


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


@A.register
class TriangleRasterize(IField, IRun):
    '''
    Name: triangle_rasterize
    Category: render
    Inputs: buffer:cf faverts:f update:t
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
        eps = ti.static(ti.get_rel_eps() * 0.2)
        screen = ti.static(V(*self.meta.shape))

        for I in ti.smart(self.pos):
            A, B, C = self.pos[I]

            scr_norm = (A - C).cross(B - A)
            if abs(scr_norm) <= eps:
                continue

            B_A = (B - A) / scr_norm
            A_C = (A - C) / scr_norm

            M = clamp(int(ti.floor(min(A, B, C) - 1)), 0, screen)
            N = clamp(int(ti.ceil(max(A, B, C) + 1)), 0, screen)
            for X in ti.grouped(ti.ndrange((M.x, N.x), (M.y, N.y))):
                X_A = X - A
                w_C = B_A.cross(X_A)
                w_B = A_C.cross(X_A)
                w_A = 1 - w_C - w_B

                is_inside = w_A >= -eps and w_B >= -eps and w_C >= -eps
                if not is_inside:
                    continue

                self.buf[X] = 1


@A.register
class FaceVertices(IField):
    '''
    Name: face_vertices
    Category: render
    Inputs: verts:f faces:f
    Output: faverts:f
    '''

    def __init__(self, verts, faces):
        assert isinstance(verts, IField)
        assert isinstance(faces, IField)

        self.verts = verts
        self.faces = faces
        self.meta = MEdit(FMeta(faces), vdims=None)

    @ti.func
    def _subscript(self, I):
        indices = self.faces[I]
        return tuple(ti.subscript(self.verts, i) for i in indices)


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
