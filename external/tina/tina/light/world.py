'''
environmental lights
'''

from tina.image import *


@ti.data_oriented
class WorldLight(metaclass=Singleton):
    def __init__(self):
        self.fac = ti.Vector.field(4, float, ())
        self.tex = ti.field(int, ())

        @ti.materialize_callback
        def init_fac():
            self.fac[None] = [0.1] * 4

    def set(self, fac, tex):
        self.fac[None] = fac
        self.tex[None] = tex

    @ti.func
    def at(self, dir):
        fac = self.fac[None]
        texid = self.tex[None]
        if texid != -1:
            dir.y, dir.z = dir.z, -dir.y  # for blender axes
            fac *= Image(texid)(*dir2tex(dir))
        return fac.xyz
