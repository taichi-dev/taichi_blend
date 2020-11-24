from . import *


@A.register
class SimpleShader(ICall):
    '''
    Name: simple_shader
    Category: render
    Inputs:
    Output: shader:n
    '''

    @ti.func
    def call(self, attr):
        return attr
