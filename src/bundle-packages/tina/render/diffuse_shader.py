from . import *


@A.register
class DiffuseShader(ICall):
    '''
    Name: diffuse_shader
    Category: render
    Inputs: light:n
    Output: shader:n
    '''

    def __init__(self, light):
        assert isinstance(light, ICall)

        self.light = light

    @ti.func
    def call(self, pos, nrm):
        ldir, lclr = self.light.call(pos)
        return max(0, lclr * nrm.dot(ldir))
