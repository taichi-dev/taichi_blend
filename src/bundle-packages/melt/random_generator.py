from . import *


@A.register
class Def(IField):
    '''
    Name: random_generator
    Category: sampler
    Inputs: min:c max:c dim:i
    Output: sample:f
    '''

    def __init__(self, min=0, max=1, dim=0):
        self.min = min
        self.max = max
        self.dim = dim

    @ti.func
    def random(self):
        return ti.random() * (self.max - self.min) + self.min

    @ti.func
    def _subscript(self, I):
        if ti.static(self.dim == 0):
            return self.random()
        else:
            return ti.Vector([self.random() for i in range(self.dim)])


