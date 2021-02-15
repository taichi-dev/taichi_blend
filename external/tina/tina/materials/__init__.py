from tina.common import *


@ti.data_oriented
class BSDFSample(namespace):
    @ti.func
    def __init__(self, outdir, pdf, color, impo=1.0):
        self.outdir = outdir
        self.pdf = pdf
        self.color = color
        self.impo = impo

    @classmethod
    def invalid(cls):
        return cls(V3(0.0), 0.0, V3(0.0), 0.0)


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


from tina.materials.disney import Disney
