from tina.common import *
from tina.geometries import *


@ti.data_oriented
class LightPool(metaclass=Singleton):
    def __init__(self, count=2**6):
        self.color = ti.Vector.field(3, float, count)
        self.pos = ti.Vector.field(3, float, count)
        self.radius = ti.field(float, count)
        self.count = ti.field(int, ())

    @ti.func
    def hit(self, ray):
        ret = namespace(dis=0.0, pdf=0.0, color=V3(0.0))
        for i in range(self.count[None]):
            t = Sphere(self.pos[i], self.radius[i]**2).intersect(ray)
            if t != 0:
                ret.dis = t
                ret.pdf = ret.dis**2 / (ti.pi * self.radius[i]**2)
                ret.color = self.color[i]
                break
        return ret

    @ti.func
    def sample(self, pos, samp):
        i = clamp(ifloor(samp.z * self.count[None]), 0, self.count[None])
        litpos = self.pos[i] + self.radius[i] * spherical(samp.x, samp.y)
        toli = litpos - pos

        dis = toli.norm()
        dir = toli / dis
        pdf = dis**2 / (ti.pi * self.radius[i]**2)
        color = self.color[i] / pdf
        return namespace(dis=dis, dir=dir, pdf=pdf, color=color)
