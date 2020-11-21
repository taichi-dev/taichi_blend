from . import *


@A.register
class Def(IField):
    '''
    Name: multiply_value
    Category: converter
    Inputs: lhs:f rhs:f
    Output: result:f
    '''

    def __init__(self, lhs, rhs):
        assert isinstance(lhs, IField)
        assert isinstance(rhs, IField)

        self.lhs = lhs
        self.rhs = rhs
        self.meta = FMeta(self.lhs)

    @ti.func
    def _subscript(self, I):
        return self.lhs[I] * self.rhs[I]


