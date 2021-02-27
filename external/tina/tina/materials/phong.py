'''
classic Phong BRDF
'''

from tina.materials import *


@ti.data_oriented
class Phong(namespace):
    @ti.func
    def __init__(self, color=V3(1.0), shineness=32.0):
        self.color = color
        self.shineness = shineness

    @ti.func
    def brdf(self, normal, sign, indir, outdir):
        m = self.shineness
        refldir = reflect(-indir, normal)
        cosor = dot_or_zero(outdir, refldir)
        ndf = cosor**m * (m + 2) / 2
        return self.color / ti.pi

    @ti.func
    def bounce(self, normal, sign, indir, samp):
        m = self.shineness
        cosor = samp.x**(1 / (m + 1))
        ndf = cosor**m * (m + 2) / 2
        refldir = reflect(-indir, normal)
        outdir = tanspace(refldir) @ spherical(cosor, samp.y)
        ret = BSDFSample.invalid()
        if outdir.dot(normal) >= 0:
            ret = BSDFSample(outdir, 1 / ti.pi, self.color)
        return ret
