from . import *


@A.register
class Def(IField):
    '''
    Name: field_shuffle
    Category: sampler
    Inputs: field:f index:vf
    Output: value:f
    '''

    def __init__(self, field, index):
        assert isinstance(field, IField)
        assert isinstance(index, IField)

        self.field = field
        self.index = index
        self.meta = FMeta(self.index)

    @ti.func
    def _subscript(self, I):
        return self.field[self.index[I]]


