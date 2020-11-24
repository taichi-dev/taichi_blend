from . import *


@A.register
class Def(IField):
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
