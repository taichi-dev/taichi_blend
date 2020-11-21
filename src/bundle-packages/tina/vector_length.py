from . import *


@A.register
class Def(IField):
    '''
    Name: vector_length
    Category: converter
    Inputs: vector:vf
    Output: length:f
    '''

    def __init__(self, field):
        assert isinstance(field, IField)

        self.field = field
        self.meta = MEdit(FMeta(self.field), vdims=())

    @ti.func
    def _subscript(self, I):
        return self.field[I].norm()


