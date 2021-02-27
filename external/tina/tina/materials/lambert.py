'''
lambert BRDF for ideal diffuse materials
'''

from tina.materials import *


@ti.data_oriented
class Lambert(namespace):
    @ti.func
    def __init__(self, color=V3(1.0)):
        self.color = color

    @ti.func
    def brdf(self, normal, sign, indir, outdir):
        cosi = dot_or_zero(indir, normal)
        coso = dot_or_zero(outdir, normal)
        return self.color / ti.pi

    @ti.func
    def bounce(self, normal, sign, indir, samp):
        outdir = tanspace(normal) @ spherical(ti.sqrt(samp.x), samp.y)
        return BSDFSample(outdir, 1 / ti.pi, self.color)


@ti.data_oriented
class Mirror(namespace):
    @ti.func
    def __init__(self, color=V3(1.0)):
        self.color = color

    @ti.func
    def brdf(self, normal, sign, indir, outdir):
        return V3(0.0)

    @ti.func
    def bounce(self, normal, sign, indir, samp):
        outdir = reflect(-indir, normal)
        return BSDFSample(outdir, inf, self.color)
