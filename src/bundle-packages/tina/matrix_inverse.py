from . import *


@A.register
class Def(IMatrix):
    '''
    Name: matrix_inverse
    Category: converter
    Inputs: trans:x
    Output: inverse:x
    '''

    def __init__(self, mat):
        assert isinstance(mat, IMatrix)

        self.mat = mat

    @ti.func
    def get_matrix(self):
        return self.mat.get_matrix().inverse()


