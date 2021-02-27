'''
albedo & normal ray tracer, used for fast preview and rendering AOV targets
'''

from tina.engine import *
from tina.sampling import *
from tina.sampling.sobol import *


@ti.data_oriented
class PreviewEngine(metaclass=Singleton):
    def __init__(self):
        SobolSampler()

    def get_rng(self, i, j):
        return SobolSampler().get_proxy(wanghash2(i, j))

    def render(self):
        SobolSampler().update()
        self._render()

    @ti.kernel
    def _render(self):
        for i, j in ti.static(GSL(FilmTable().nx, FilmTable().ny)):
            rng = self.get_rng(i, j)

            albedo = V3(0.0)
            normal = V3(0.0)

            dx, dy = random2(rng)
            x = (i + dx) / FilmTable().nx * 2 - 1
            y = (j + dy) / FilmTable().ny * 2 - 1
            ray = Camera().generate(x, y)
            hit = BVHTree().intersect(ray, -1)

            if hit.hit == 1:
                hitpos, normal, sign, material = ModelPool().get_geometries(hit, ray)
                albedo = material.basecolor

            FilmTable()[1, i, j] += V34(albedo, 1.0)
            FilmTable()[2, i, j] += V34(normal, 1.0)
