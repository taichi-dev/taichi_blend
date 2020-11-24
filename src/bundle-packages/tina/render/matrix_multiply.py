from . import *


@A.register
class Def(IMatrix):
    '''
    Name: matrix_multiply
    Category: converter
    Inputs: first:x second:x
    Output: combined:x
    '''

    def __init__(self, first, second):
        assert isinstance(first, IMatrix)
        assert isinstance(second, IMatrix)

        self.first = first
        self.second = second

    @ti.func
    def get_matrix(self):
        return self.second.get_matrix() @ self.first.get_matrix()


