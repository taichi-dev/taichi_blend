from . import *


@A.register
class SimpleShader(ICall):
    '''
    Name: simple_shader
    Category: render
    Inputs: fapos:f fanrm:f pers:x inv_pers:x
    Output: shader:n
    '''

    def __init__(self, pos, nrm, pers, inv_pers):
        assert isinstance(pos, IField)
        assert isinstance(nrm, IField)

        self.pos = pos
        self.nrm = nrm
        self.pers = pers
        self.inv_pers = inv_pers

    @ti.func
    def call(self, I, wei):
        posa, posb, posc = self.pos[I]
        wei /= V(*[self.pers.apply(pos, 1)[1] for pos in [posa, posb, posc]])
        wei /= wei.x + wei.y + wei.z
        pos = wei.x * posa + wei.y * posb + wei.z * posc

        nrma, nrmb, nrmc = self.nrm[I]
        nrm = wei.x * nrma + wei.y * nrmb + wei.z * nrmc
        nrm = nrm.normalized()

        return max(0, nrm.dot(V(1.0, 1.0, 1.0).normalized()))
