from . import *


@A.register
class TriangleRasterize(IRun, IField):
    '''
    Name: triangle_rasterize
    Category: render
    Inputs: buffer:cf faverts:f faattrs:f shader:n update:t
    Output: buffer:cf update:t
    '''

    def __init__(self, buf, pos, attr, shader, chain):
        super().__init__(chain)

        assert isinstance(buf, IField)
        assert isinstance(pos, IField)
        assert isinstance(attr, IField)
        assert isinstance(shader, ICall)

        self.buf = buf
        self.pos = pos
        self.attr = attr
        self.meta = FMeta(buf)
        self.shader = shader

    @ti.func
    def _subscript(self, I):
        return self.buf[I]

    @ti.kernel
    def _run(self):
        eps = ti.static(ti.get_rel_eps() * 0.2)
        screen = ti.static(V(*self.meta.shape))

        for I in ti.smart(self.pos):
            A, B, C = self.pos[I]
            a_A, a_B, a_C = self.attr[I]

            scr_norm = (A - C).cross(B - A)
            if scr_norm <= eps:
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

                color = self.shader.call(a_A * w_A + a_B * w_B + a_C * w_C)
                self.buf[X] = color
