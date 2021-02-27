from . import *


@A.register
class Def(IField):
    '''
    Name: const_field
    Category: sampler
    Inputs: value:c
    Output: field:f
    '''

    def __init__(self, value):
        self.value = value

    @ti.func
    def _subscript(self, I):
        return self.value
