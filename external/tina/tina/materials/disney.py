from tina.materials import *
from tina.materials.microfacet import *


@ti.data_oriented
class Disney(namespace):
    @ti.func
    def __init__(self,
            basecolor=V3(1.0),
            metallic=0.0,
            roughness=1.0,
            specular=0.5,
            specularTint=0.4,
            subsurface=0.0,
            sheen=0.0,
            sheenTint=0.4,
            clearcoat=0.0,
            clearcoatGloss=0.5,
            transmission=0.0,
            ior=1.45):

        self.basecolor = basecolor
        self.metallic = metallic
        self.subsurface = subsurface
        self.roughness = roughness
        self.specular = specular
        self.specularTint = specularTint
        self.sheen = sheen
        self.sheenTint = sheenTint
        self.clearcoat = clearcoat
        self.clearcoatGloss = clearcoatGloss
        self.transmission = transmission
        self.ior = ior

        self.tintcolor = V3(1.0)
        luminance = self.basecolor.dot(V(0.3, 0.6, 0.1))
        if luminance > eps:
            self.tintcolor = self.basecolor / luminance
        self.speccolor = lerp(self.metallic, self.specular * 0.08 * lerp(
            self.specularTint, V3(1.0), self.tintcolor), self.basecolor)
        self.sheencolor = lerp(self.sheenTint, V3(1.0), self.tintcolor)

        self.alpha = max(0.001, self.roughness**2)
        self.clearcoatAlpha = lerp(self.clearcoatGloss, 0.1, 0.001)

    @ti.func
    def brdf(self, normal, sign, indir, outdir):
        etai, etao = 1.0, self.ior
        if sign < 0:
            etai = self.ior
            etao = 1.0
        eta = etai / etao

        halfdir = (indir + outdir).normalized()
        cosi = indir.dot(normal)
        coso = outdir.dot(normal)
        cosh = dot_or_zero(halfdir, normal)
        cosoh = dot_or_zero(halfdir, outdir)

        result = V3(0.0)
        if coso < 0:
            if cosi >= 0:
                Ds = GTR2(cosh, self.alpha)
                fdf = dielectricFresnel(etao, etai, cosoh)
                transmit = 1 / ti.pi * self.basecolor * (1 - fdf) * Ds
                result = transmit * (1 - self.metallic) * self.transmission

        else:
            Fi = schlickFresnel(cosi)
            Fo = schlickFresnel(coso)
            Fd90 = 0.5 + 2 * cosoh**2 * self.roughness
            Fd = lerp(Fi, 1.0, Fd90) * lerp(Fo, 1.0, Fd90)

            Fss90 = cosoh**2 * self.roughness
            Fss = lerp(Fi, 1.0, Fss90) * lerp(Fo, 1.0, Fss90)
            ss = 1.25 * (Fss * (1 / (cosi + coso) - 0.5) + 0.5)

            Foh = schlickFresnel(cosoh)
            Fsheen = Foh * self.sheen * self.sheencolor

            fdf = dielectricFresnel(etao, etai, cosoh)

            Ds = GTR2(cosh, self.alpha)
            Fs = lerp(Foh, self.speccolor, V3(1))
            Gs = smithGGX(cosi, self.alpha) * smithGGX(coso, self.alpha)

            Dr = GTR1(cosh, self.clearcoatAlpha)
            Gr = smithGGX(cosi, 0.25) * smithGGX(coso, 0.25)
            Fr = lerp(Foh, 0.04, 1.0)

            diffuse = 1 / ti.pi * lerp(self.subsurface, Fd, ss) \
                    * self.basecolor + Fsheen
            specular = Gs * Fs * Ds + 0.25 * self.clearcoat * Gr * Fr * Dr
            transmit = 1 / ti.pi * fdf * Ds * self.basecolor

            result = diffuse * (1 - self.metallic) * (1 - self.transmission)
            result += transmit * (1 - self.metallic) * self.transmission
            result += specular * (1 - self.transmission)

        return result

    @ti.func
    def stupid_bounce(self, normal, sign, indir, samp):
        outdir = tanspace(normal) @ spherical(ti.sqrt(samp.x), samp.y)
        brdf = self.brdf(normal, sign, indir, outdir)
        return BSDFSample(outdir, Vavg(brdf), brdf * ti.pi)

    @ti.func
    def bounce(self, normal, sign, indir, samp):
        result = BSDFSample.invalid()

        etai, etao = 1.0, self.ior
        if sign < 0:
            etai = self.ior
            etao = 1.0
        eta = etai / etao

        choice = Choice(samp.z)
        specrate = lerp(self.transmission, lerp(self.metallic, 
            self.specular * 0.08, 1.0), 1.0)
        coatrate = 0.04 * self.clearcoat

        specrate = lerp(specrate, 0.1, 1.0)
        if coatrate != 0:
            coatrate = lerp(coatrate, 0.1, 1.0)

        if choice(coatrate):
            alpha = self.clearcoatAlpha
            halfdir = tanspace(normal) @ sample_GTR1(samp.x, samp.y, alpha)
            outdir = reflect(-indir, halfdir)

            cosi = indir.dot(normal)
            coso = outdir.dot(normal)
            cosh = dot_or_zero(halfdir, normal)
            cosoh = dot_or_zero(halfdir, outdir)
            if cosoh > 0:
                Dr = GTR1(cosh, alpha)
                Foh = schlickFresnel(cosoh)
                Gr = smithGGX(cosi, 0.25) * smithGGX(coso, 0.25)
                Fr = lerp(Foh, 0.04, 1.0)

                result.outdir = outdir
                partial = self.clearcoat * Gr * Fr * coso * cosi
                result.pdf = Dr * partial
                result.color = partial / choice.pdf
                result.impo = 1

        elif choice(specrate):
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

        else:
            outdir = tanspace(normal) @ spherical(ti.sqrt(samp.x), samp.y)

            halfdir = (indir + outdir).normalized()
            cosi = indir.dot(normal)
            coso = outdir.dot(normal)
            cosh = dot_or_zero(halfdir, normal)
            cosoh = dot_or_zero(halfdir, outdir)

            Fi = schlickFresnel(cosi)
            Fo = schlickFresnel(coso)
            Fd90 = 0.5 + 2 * cosoh**2 * self.roughness
            Fd = lerp(Fi, 1.0, Fd90) * lerp(Fo, 1.0, Fd90)

            Fss90 = cosoh**2 * self.roughness
            Fss = lerp(Fi, 1.0, Fss90) * lerp(Fo, 1.0, Fss90)
            ss = 1.25 * (Fss * (1 / (cosi + coso) - 0.5) + 0.5)

            Foh = schlickFresnel(cosoh)
            Fsheen = Foh * self.sheen * self.sheencolor

            diffuse = 1 / ti.pi * lerp(self.subsurface, Fd, ss) \
                    * self.basecolor + Fsheen

            result.outdir = outdir
            result.pdf = 1 / ti.pi
            result.color = diffuse * ti.pi * \
                    (1 - self.metallic) * (1 - self.transmission) / choice.pdf
            result.impo = 1

        return result
