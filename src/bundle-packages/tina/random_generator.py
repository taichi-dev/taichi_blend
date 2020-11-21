from . import *


@A.register
class Def(IField):
    '''
    Name: random_generator
    Category: texture
    Inputs: dim:i
    Output: sample:f
    '''

    def __init__(self, dim=0):
        self.dim = dim

    @ti.func
    def random(self):
        return ti.random()

    @ti.func
    def _subscript(self, I):
        if ti.static(self.dim == 0):
            return self.random()
        else:
            return ti.Vector([self.random() for i in range(self.dim)])


