from . import *


@A.register
class Def(IField):
    '''
    Name: affine_transform
    Category: converter
    Inputs: vector:vf matrix:vf offset:vf
    Output: result:vf
    '''

    def __init__(self, vec, mat, off):
        assert isinstance(vec, IField)
        assert isinstance(mat, IField)
        assert isinstance(off, IField)

        self.vec = vec
        self.mat = mat
        self.off = off
        self.meta = FMeta(self.vec)

    @ti.func
    def _subscript(self, I):
        return self.mat[I] @ self.vec[I] + self.off[I]


