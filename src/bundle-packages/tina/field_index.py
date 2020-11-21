from . import *


@A.register
class Def(IField):
    '''
    Name: field_index
    Category: parameter
    Inputs:
    Output: index:vf
    '''

    def __init__(self):
        pass

    @ti.func
    def _subscript(self, I):
        return I


