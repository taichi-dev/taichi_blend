from . import *


@A.register
class ApplyTransform(IField):
    '''
    Name: apply_transform
    Category: converter
    Inputs: verts:f trans:x affine:b
    Output: verts:f
    '''

    def __init__(self, pos, mat, is_affine=True):
        assert isinstance(pos, IField)
        assert isinstance(mat, IMatrix)

        self.pos = pos
        self.mat = mat
        self.is_affine = is_affine
        self.meta = FMeta(self.pos)

    @ti.func
    def _subscript(self, I):
        pos, wei = self.mat.apply(self.pos[I], ti.static(int(self.is_affine)))
        if ti.static(self.is_affine):
            return pos / wei
        else:
            return pos

