from . import *


@A.register
class DiffuseShader(ICall):
    '''
    Name: diffuse_shader
    Category: shader
    Inputs: light:n color:f
    Output: shader:n
    '''

    def __init__(self, light, color):
        assert isinstance(light, ICall)

        self.light = light
        self.color = color

    @ti.func
    def call(self, pos, nrm):
        ldir, lclr = self.light.call(pos)
        strength = max(0, nrm.dot(ldir))
        return lclr * self.color[None] * strength
