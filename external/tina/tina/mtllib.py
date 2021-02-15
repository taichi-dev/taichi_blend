from tina.image import *
from tina.materials import *


@ti.data_oriented
class ParameterPair:
    def __init__(self, count):
        self.fac = ti.Vector.field(4, float, count)
        self.tex = ti.field(int, count)

    def load(self, i, fac, tex):
        if fac is None:
            fac = 1.0
        if not isinstance(fac, (tuple, list)):
            fac = [fac, fac, fac, fac]
        self.fac[i] = fac
        if tex is None:
            self.tex[i] = -1
        else:
            imgid = ImagePool().load(tex)
            self.tex[i] = imgid
    
    @ti.func
    def get(self, mtlid, texcoord):
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
        self.count = ti.field(int, ())

    def load(self, materials):
        for i, material in enumerate(materials):
            b, bt, m, mt, r, rt = material
            self.basecolor.load(i, b, bt)
            self.metallic.load(i, m, mt)
            self.roughness.load(i, r, rt)
        self.count[None] = len(materials)

    def get(self, mtlid, texcoord):
        material = Disney(
                self.basecolor.get(mtlid, texcoord).xyz,
                self.metallic.get(mtlid, texcoord).x,
                self.roughness.get(mtlid, texcoord).x,
                )
        return material
