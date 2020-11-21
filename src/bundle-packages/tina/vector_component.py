from . import *


@A.register
class FVChannel(IField):
    '''
    Name: vector_component
    Category: converter
    Inputs: vector:vf channel:i
    Output: value:f
    '''

    def __init__(self, field, channel):
        assert isinstance(field, IField)

        self.field = field
        self.channel = channel
        self.meta = MEdit(FMeta(self.field), vdims=())

    @ti.func
    def _subscript(self, I):
        return self.field[I][self.channel]
