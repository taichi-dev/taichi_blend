from . import *


@A.register
class Def(IField):
    '''
    Name: gaussian_dist
    Category: sampler
    Inputs: center:c2 radius:c height:c
    Output: sample:f
    '''

    def __init__(self, center, radius, height=1):
        self.center = tovector(center)
        self.radius = radius
        self.height = height

    @ti.func
    def _subscript(self, I):
        r2 = (I - self.center).norm_sqr() / self.radius**2
        return self.height * ti.exp(-r2)


