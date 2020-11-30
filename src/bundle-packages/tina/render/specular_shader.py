from . import *


@A.register
class SpecularShader(ICall):
    '''
    Name: specular_shader
    Category: shader
    Inputs: light:n view:x color:f shineness:f
    Output: shader:n
    '''

    def __init__(self, light, view, color, shineness):
        assert isinstance(light, ICall)
        assert isinstance(view, IMatrix)

        self.view = view
        self.light = light
        self.color = color
        self.shineness = shineness

    @ti.func
    def call(self, pos, nrm):
        ldir, lclr = self.light.call(pos)
        campos = self.view.applies(V(0, 0, 0), 1)
        viewdir = campos - pos

        half = ((viewdir - ldir) / 2).normalized()
        strength = pow(nrm.dot(half), self.shineness[None])
        return lclr * self.color[None] * strength
