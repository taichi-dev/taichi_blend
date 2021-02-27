from . import *


@A.register
class Def(IField):
    '''
    Name: uniform_field
    Category: sampler
    Inputs: value:f
    Output: field:f
    '''

    def __init__(self, value):
        assert isinstance(value, IField)

        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value[None]
