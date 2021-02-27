'''
unidirectional path integrator, fast for regular lighting conditions
'''

from tina.engine import *
from tina.sampling import *
from tina.sampling.sobol import *


@ti.func
def power_heuristic(a, b):
    a = clamp(a, eps, inf)**2
    b = clamp(b, eps, inf)**2
    return a / (a + b)


@ti.func
def path_trace(r, rng):
    avoid = -1
    depth = 0
    result = V3(0.0)
    throughput = V3(1.0)
    last_brdf_pdf = 0.0

    while depth < 5 and Vany(throughput > 0) and Vany(r.d != 0):
        depth += 1

        r.d = r.d.normalized()
        hit = BVHTree().intersect(r, avoid)

        lit = LightPool().hit(r)
        if lit.hit != 0 and (hit.hit == 0 or lit.dis < hit.depth):
            mis = power_heuristic(last_brdf_pdf, lit.pdf)
            direct_li = mis * lit.color
            result += throughput * direct_li

        if hit.hit == 0:
            result += throughput * WorldLight().at(r.d)
            break

        avoid = hit.index
        hitpos, normal, sign, material = ModelPool().get_geometries(hit, r)

        sign = -r.d.dot(normal)
        if sign < 0:
            normal = -normal

        li = LightPool().sample(hitpos, random3(rng))
        if Vany(li.color > 0):
            occ = BVHTree().intersect(Ray(hitpos, li.dir), avoid)
            if occ.hit == 0 or occ.depth > li.dis:
                brdf_clr = material.brdf(normal, sign, -r.d, li.dir)
                brdf_pdf = Vavg(brdf_clr)
                mis = power_heuristic(li.pdf, brdf_pdf)
                direct_li = mis * li.color * brdf_clr * dot_or_zero(normal, li.dir)
                result += throughput * direct_li

        brdf = material.bounce(normal, sign, -r.d, random3(rng))
        throughput *= brdf.color
        r.o = hitpos
        r.d = brdf.outdir
        last_brdf_pdf = brdf.pdf

    return result


@ti.data_oriented
class PathEngine(metaclass=Singleton):
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
            self.do_render(rng, i, j)

    @ti.func
    def do_render(self, rng, i, j):
        dx, dy = random2(rng)
        x = (i + dx) / FilmTable().nx * 2 - 1
        y = (j + dy) / FilmTable().ny * 2 - 1
        ray = Camera().generate(x, y)

        clr = path_trace(ray, rng)
        FilmTable()[0, i, j] += V34(clr, 1.0)

    '''
    def render_tile(self, i, j, samples):
        SobolSampler().update()
        self._render_tile(i, j, samples)

    @ti.kernel
    def _render_tile(self, i: int, j: int, samples: int):
        for id in range(64**3):
            m = id % 64
            l = id // 64 % 64
            k = id // 64**2

            x = i * 64 + k
            y = j * 64 + l
            if x > FilmTable().nx:
                continue
            if y > FilmTable().ny:
                continue
            if m > samples:
                continue
            rng = SobolSampler().get_proxy(wanghash3(x, y, m))
            Stack().set(id)
            self.do_render(rng, x, y)
            Stack().unset()

    def render_final(self, nsamples):
        for i in range((FilmTable().nx + 63) // 64):
            for j in range((FilmTable().ny + 63) // 64):
                print('[TinaPath] rendering tile', i, j)
                samples = nsamples
                while samples > 0:
                    self.render_tile(i, j, samples)
                    samples -= 64
    '''
