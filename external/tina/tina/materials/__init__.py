'''
different kind of materials
'''

from tina.common import *


@ti.data_oriented
class BSDFSample(namespace):
    @ti.func
    def __init__(self, outdir, pdf, color):
        self.outdir = outdir
        self.pdf = pdf
        self.color = color

    @classmethod
    def invalid(cls):
        return cls(V3(0.0), 0.0, V3(0.0))


@ti.data_oriented
class Choice(namespace):
    @ti.func
    def __init__(self, w):
        self.pdf = 1.0
        self.w = w

    @ti.func
    def call(self, r):
        ret = ti.random() < r
        if ret:
            self.pdf *= r
        else:
            self.pdf *= 1 - r
        return ret

    @ti.func
    def __call__(self, r):
        ret = 0
        if self.w < r:
            self.w /= r
            self.pdf *= r
            ret = 1
        else:
            self.w = (self.w - r) / (1 - r)
            self.pdf *= 1 - r
            ret = 0
        return ret


#from tina.materials.disney import Disney
#from tina.materials.glossy import Glossy
#from tina.materials.lambert import Lambert, Mirror
#from tina.materials.phong import Phong
