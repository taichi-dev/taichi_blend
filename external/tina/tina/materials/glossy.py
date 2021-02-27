'''
Not working Glossy BRDF
'''

from tina.materials import *
from tina.materials.microfacet import *


@ti.data_oriented
class Glossy(namespace):
    @ti.func
    def __init__(self, basecolor=V3(1.0), roughness=0.4):
        self.basecolor = basecolor
        self.roughness = roughness

        self.alpha = max(0.001, self.roughness**2)

    @ti.func
    def brdf(self, normal, sign, indir, outdir):
        halfdir = (indir + outdir).normalized()
        cosi = indir.dot(normal)
        coso = outdir.dot(normal)
        cosh = dot_or_zero(halfdir, normal)
        cosoh = dot_or_zero(halfdir, outdir)

        Foh = schlickFresnel(cosoh)
        fdf = dielectricFresnel(etao, etai, cosoh)

        Ds = GTR2(cosh, self.alpha)
        Fs = lerp(Foh, self.basecolor, V3(1))
        Gs = smithGGX(cosi, self.alpha) * smithGGX(coso, self.alpha)

        return Gs * Fs * Ds

    def bounce(self, normal, sign, indir, samp):
        alpha = self.alpha
        halfdir = tanspace(normal) @ sample_GTR2(samp.x, samp.y, alpha)
        outdir = reflect(-indir, halfdir)

        cosi = dot_or_zero(indir, normal)
        coso = dot_or_zero(outdir, normal)
        cosh = dot_or_zero(halfdir, normal)
        cosoh = dot_or_zero(halfdir, outdir)
        if cosoh > 0 and coso > 0:
            Ds = GTR2(cosh, alpha)

            if choice(self.transmission):
                fdf = dielectricFresnel(etao, etai, cosoh)
                reflrate = lerp(fdf, 0.2, 1.0)

                if choice(reflrate):
                    result.outdir = outdir
                    result.pdf = Ds * fdf
                    result.color = self.basecolor * \
                            fdf * self.transmission / choice.pdf
                    result.impo = 1

                else:
                    has_r, outdir = refract(-indir, halfdir, eta)
                    if has_r:
                        result.outdir = outdir
                        result.pdf = Ds * (1 - fdf)
                        result.color = self.basecolor * (1 - fdf) \
                                * self.transmission / choice.pdf
                        result.impo = 1

            else:
                Foh = schlickFresnel(cosoh)
                Fs = lerp(Foh, self.speccolor, V3(1.0))
                Gs = smithGGX(cosi, alpha) * smithGGX(coso, alpha)

                result.outdir = outdir
                partial = Gs * 2 * coso * lerp(alpha, 2 * cosi, 1.0)
                result.pdf = Ds * Vavg(Fs) * partial
                result.color = Fs * partial \
                        * (1 - self.transmission) / choice.pdf
                result.impo = 1
