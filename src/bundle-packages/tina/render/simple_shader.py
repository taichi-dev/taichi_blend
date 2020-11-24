from . import *


@A.register
class SimpleShader(ICall):
    '''
    Name: simple_shader
    Category: render
    Inputs: inv_pers:x
    Output: shader:n
    '''

    def __init__(self, inv_pers):
        self.inv_pers = inv_pers

    @ti.func
    def call(self, attr):
        pos = attr
        pos, posw = self.inv_pers.apply(pos, 1)
        return pos / posw
