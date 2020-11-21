from . import *


@A.register
class Def(IField):
    '''
    Name: field_bilerp
    Category: sampler
    Inputs: field:f pos:vf
    Output: value:f
    '''

    def __init__(self, field, pos):
        assert isinstance(field, IField)
        assert isinstance(index, IField)

        self.field = field
        self.pos = pos
        self.meta = FMeta(self.pos)

    @ti.func
    def _subscript(self, I):
        return bilerp(self.field, self.pos[I])


