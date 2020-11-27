from . import *


@A.register
class Def(IMatrix):
    '''
    Name: matrix_inverse
    Category: converter
    Inputs: trans:x
    Output: inverse:x
    '''

    def __init__(self, src):
        assert isinstance(src, IMatrix)

        self.src = src

    @ti.func
    def get_matrix(self):
        return self.src.get_inv_matrix()

    @ti.func
    def get_inv_matrix(self):
        return self.src.get_matrix()


