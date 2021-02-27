'''
point and area lights
'''

from tina.common import *
from tina.geometries import *


@ti.data_oriented
class LightPool(metaclass=Singleton):
    TYPES = {'POINT': 1, 'AREA': 2}

    def __init__(self, count=2**6):
        self.color = ti.Vector.field(3, float, count)
        self.pos = ti.Vector.field(3, float, count)
        self.axes = ti.Matrix.field(3, 3, float, count)
        self.size = ti.field(float, count)
        self.type = ti.field(int, count)
        self.count = ti.field(int, ())

        #'''
        @ti.materialize_callback
        def default_light():
            self.color[0] = [32, 32, 32]
            self.pos[0] = [1, 2, 3]
            self.size[0] = 0.5
            self.type[0] = self.TYPES['POINT']
            self.count[None] = 1
        #'''

    def clear(self):
        self.count[None] = 0

    def add(self, world, color, size, type):
        i = self.count[None]

        pos = world @ np.array([0, 0, 0, 1])
        pos = pos[:3] / pos[3]

        axes = world[:3, :3]

        self.type[i] = self.TYPES[type]
        self.color[i] = color.tolist()
        self.pos[i] = pos.tolist()
        self.axes[i] = axes.tolist()
        self.size[i] = size

        self.count[None] = i + 1
        return i

    @ti.func
    def hit(self, ray):
        ret = namespace(hit=0, dis=inf, pdf=0.0, color=V3(0.0))

        for i in range(self.count[None]):
            type = self.type[i]
            color = self.color[i]
            pos = self.pos[i]
            size = self.size[i]
            axes = self.axes[i]

            t = 0.0
            area = 0.0
            if type == self.TYPES['POINT']:
                t = Sphere(pos, size**2).intersect(ray)
                area = ti.pi * size**2
            elif type == self.TYPES['AREA']:
                dirx = axes @ V(size, 0.0, 0.0)
                diry = axes @ V(0.0, size, 0.0)
                hit = Area(pos, dirx, diry).intersect(ray)
                if hit.hit:
                    t = hit.depth
                    area = 4 * size**2

            if 0 < t < ret.dis:
                ret.dis = t
                ret.pdf = ret.dis**2 / area
                ret.color = color
                ret.hit = 1
                break
        return ret

    @ti.func
    def _sample(self, hitpos, samp):
        i = clamp(ifloor(samp.z * self.count[None]), 0, self.count[None])

        type = self.type[i]
        color = self.color[i]
        pos = self.pos[i]
        size = self.size[i]
        axes = self.axes[i]

        litpos = V3(inf)
        norm = V3(0.0)
        area = 0.0

        if type == self.TYPES['POINT']:
            disp = spherical(samp.x, samp.y)
            litpos = pos + size * disp
            area = ti.pi * size**2
        elif type == self.TYPES['AREA']:
            disp = axes @ V(samp.x * 2 - 1, samp.y * 2 - 1, 0.0)
            norm = axes @ V(0.0, 0.0, 1.0)
            litpos = pos + size * disp
            area = 4 * size**2

        toli = litpos - hitpos
        dis = toli.norm()
        dir = toli / dis
        pdf = dis**2 / area
        color = color / pdf
        if Vany(norm != 0):
            color *= dot_or_zero(norm, dir)
        return namespace(dis=dis, dir=dir, pdf=pdf, color=color)

    @ti.func
    def sample(self, hitpos, samp):
        ret = namespace(dis=inf, dir=V3(0.0), pdf=0.0, color=V3(0.0))
        if self.count[None] != 0:
            ret = self._sample(hitpos, samp)
        return ret
