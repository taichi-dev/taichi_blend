from . import *


@A.register
class TriangleInterp(ICall):
    '''
    Name: triangle_interp
    Category: render
    Inputs: fapos:f fanrm:f pers:x shader:n
    Output: interp:n
    '''

    def __init__(self, pos, nrm, pers, shader):
        assert isinstance(pos, IField)
        assert isinstance(nrm, IField)
        assert isinstance(shader, ICall)

        self.pos = pos
        self.nrm = nrm
        self.pers = pers
        self.shader = shader

    @ti.func
    def call(self, I, wei):
        posa, posb, posc = self.pos[I]
        wei /= V(*[self.pers.apply(pos, 1)[1] for pos in [posa, posb, posc]])
        wei /= wei.x + wei.y + wei.z
        pos = wei.x * posa + wei.y * posb + wei.z * posc

        nrma, nrmb, nrmc = self.nrm[I]
        nrm = wei.x * nrma + wei.y * nrmb + wei.z * nrmc
        nrm = nrm.normalized()

        return self.shader.call(pos, nrm)
