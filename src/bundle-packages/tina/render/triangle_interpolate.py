from . import *


@A.register
class TriangleInterpolate(ICall):
    '''
    Name: triangle_interpolate
    Category: render
    Inputs:
    Output: shader:n
    '''
    
    @ti.func
    def call(self, wa, wb, wc):
        return V(wa, wb, wc)
