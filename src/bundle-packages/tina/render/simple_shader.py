from . import *


@A.register
class SimpleShader(ICall):
    '''
    Name: simple_shader
    Category: render
    Inputs: fapos:f fanrm:f inv_pers:x
    Output: shader:n
    '''

    def __init__(self, pos, nrm, inv_pers):
        assert isinstance(pos, IField)
        assert isinstance(nrm, IField)

        self.pos = pos
        self.nrm = nrm
        self.inv_pers = inv_pers

    @ti.func
    def call(self, I, wei):
        posa, posb, posc = self.pos[I]
        nrma, nrmb, nrmc = self.nrm[I]
        pos = wei.x * posa + wei.y * posb + wei.z * posc
        pos, posw = self.inv_pers.apply(pos, 0)
        pos /= posw

        nrm = wei.x * nrma + wei.y * nrmb + wei.z * nrmc
        nrm = nrm.normalized()

        return max(0, nrm.dot(V(1.0, 1.0, 1.0).normalized()))
