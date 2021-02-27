'''
material table, storing their factor and texture informations
'''

from tina.image import *
from tina.materials.disney import *


@ti.data_oriented
class ParameterPair:
    def __init__(self, count):
        self.fac = ti.Vector.field(4, float, count)
        self.tex = ti.field(int, count)

    def load(self, i, fac, tex):
        if fac is None:
            fac = 1.0
        if isinstance(fac, np.ndarray):
            if len(fac.shape):
                fac = list(fac)
            else:
                fac = float(fac)
        if not isinstance(fac, (tuple, list)):
            fac = [fac, fac, fac, fac]
        if isinstance(fac, (tuple, list)) and len(fac) == 3:
            fac = list(fac) + [1.0]
        self.fac[i] = fac
        self.tex[i] = tex
    
    @ti.func
    def get(self, mtlid, texcoord, default=1.0):
        fac = V4(default)
        if mtlid != -1:
            fac = self.fac[mtlid]
            texid = self.tex[mtlid]
            if texid != -1:
                fac *= Image(texid)(*texcoord)
        return fac


@ti.data_oriented
class MaterialPool(metaclass=Singleton):
    def __init__(self, count=2**6):
        self.basecolor = ParameterPair(count)
        self.metallic = ParameterPair(count)
        self.roughness = ParameterPair(count)
        self.specular = ParameterPair(count)
        self.specularTint = ParameterPair(count)
        self.subsurface = ParameterPair(count)
        self.sheen = ParameterPair(count)
        self.sheenTint = ParameterPair(count)
        self.clearcoat = ParameterPair(count)
        self.clearcoatGloss = ParameterPair(count)
        self.transmission = ParameterPair(count)
        self.ior = ParameterPair(count)
        self.count = ti.field(int, ())

    def load(self, materials):
        for i, material in enumerate(materials):
            params = [
                self.basecolor,
                self.metallic,
                self.roughness,
                self.specular,
                self.specularTint,
                self.subsurface,
                self.sheen,
                self.sheenTint,
                self.clearcoat,
                self.clearcoatGloss,
                self.transmission,
                self.ior,
            ]
            for (fac, tex), param in zip(material, params):
                param.load(i, fac, tex)

        self.count[None] = len(materials)

    @ti.func
    def get(self, mtlid, texcoord):
        material = Disney(
                self.basecolor.get(mtlid, texcoord, 0.8).xyz,
                self.metallic.get(mtlid, texcoord, 0.0).x,
                self.roughness.get(mtlid, texcoord, 0.4).x,
                self.specular.get(mtlid, texcoord, 0.5).x,
                self.specularTint.get(mtlid, texcoord, 0.4).x,
                self.subsurface.get(mtlid, texcoord, 0.0).x,
                self.sheen.get(mtlid, texcoord, 0.0).x,
                self.sheenTint.get(mtlid, texcoord, 0.4).x,
                self.clearcoat.get(mtlid, texcoord, 0.0).x,
                self.clearcoatGloss.get(mtlid, texcoord, 0.5).x,
                self.transmission.get(mtlid, texcoord, 0.0).x,
                self.ior.get(mtlid, texcoord, 1.45).x,
                )
        return material
