'''
film that records the rendering result
'''

from tina.image import *


@ti.data_oriented
class FilmTable(metaclass=Singleton):
    is_taichi_class = True

    def __init__(self, size=2**21, count=3):  # 96 MB
        self.res = ti.Vector.field(2, int, ())
        self.root = ti.Vector.field(4, float, (count, size))

    @property
    @ti.pyfunc
    def nx(self):
        return self.res[None].x

    @property
    @ti.pyfunc
    def ny(self):
        return self.res[None].y

    @nx.setter
    @ti.pyfunc
    def nx(self, value):
        self.res[None].x = nx

    @ny.setter
    @ti.pyfunc
    def ny(self, value):
        self.res[None].y = ny

    @ti.func
    def subscript(self, id, x, y):
        index = x * self.ny + y
        return self.root[id, index]

    def set_size(self, nx, ny):
        self.res[None] = [nx, ny]

    def clear(self, id=0):
        self.root.fill(0)

    def get_image(self, id=0):
        arr = np.empty((self.nx, self.ny, 4), np.float32)
        self._get_image(id, arr)
        return arr

    @ti.kernel
    def _get_image(self, id: int, arr: ti.ext_arr()):
        nx, ny = self.res[None]
        for x, y in ti.ndrange(nx, ny):
            val = self[id, x, y]
            if val.w != 0:
                val.xyz /= val.w
                val.w = 1.0
            else:
                val = V(0.9, 0.4, 0.9, 0.0)
            for k in ti.static(range(4)):
                arr[x, y, k] = val[k]

    @ti.kernel
    def fast_export_image(self, out: ti.ext_arr(), id: int):
        shape = self.res[None]
        for x, y in ti.ndrange(shape.x, shape.y):
            base = (y * shape.x + x) * 3
            I = V(x, y)
            val = self[id, x, y]
            if val.w != 0:
                val.xyz /= val.w
            else:
                val.xyz = V(0.9, 0.4, 0.9)
            r, g, b = val.xyz
            out[base + 0] = r
            out[base + 1] = g
            out[base + 2] = b
