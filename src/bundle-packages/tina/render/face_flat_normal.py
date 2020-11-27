from . import *


@A.register
class FaceFlatNormal(IField):
    '''
    Name: face_flat_normal
    Category: render
    Inputs: faverts:f
    Output: fanorms:f
    '''

    def __init__(self, pos):
        assert isinstance(pos, IField)

        self.pos = pos
        self.meta = MEdit(FMeta(pos), vdims=None)

    @ti.func
    def _subscript(self, I):
        a, b, c = self.pos[I]
        n = (a - c).cross(b - a).normalized()
        return n, n, n
