from . import *


@A.register
class DiffuseShader(ICall):
    '''
    Name: diffuse_shader
    Category: render
    Inputs:
    Output: shader:n
    '''

    def __init__(self):
        pass

    @ti.func
    def call(self, pos, nrm):
        return max(0, nrm.dot(V(1.0, 1.0, 1.0).normalized()))
