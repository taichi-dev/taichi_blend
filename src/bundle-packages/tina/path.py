from .common import *
from .advans import *
import ezprof


EPS = 1e-6
INF = 1e8


@ti.func
def sphere_intersect(s_id, s_pos, s_rad, r_org, r_dir):
    i_t = INF
    op = s_pos - r_org
    b = op.dot(r_dir)
    det = b**2 - op.norm_sqr() + s_rad**2
    if det >= 0:
        det = ti.sqrt(det)
        i_t = b - det
        if i_t <= EPS:
            i_t = b + det
            if i_t <= EPS:
                i_t = INF
    i_pos = r_org + i_t * r_dir
    i_nrm = (i_pos - s_pos).normalized()
    i_tex = V(0., 0.)  # NotImplemented
    return i_t, s_id, i_pos, i_nrm, i_tex


@ti.func
def triangle_intersect(id, v0, v1, v2, ro, rd):
    e1 = v1 - v0
    e2 = v2 - v0
    p = rd.cross(e2)
    det = e1.dot(p)
    r = ro - v0

    t, u, v = INF, 0.0, 0.0
    ipos, inrm, itex = V(0.0, 0.0, 0.0), V(0.0, 0.0, 0.0), V(0.0, 0.0)

    if det < 0:
        r = -r
        det = -det

    if det >= EPS:
        u = r.dot(p)
        if 0 <= u <= det:
            q = r.cross(e1)
            v = rd.dot(q)
            if v >= 0 and u + v <= det:
                t = e2.dot(q)
                det = 1 / det
                t *= det
                u *= det
                v *= det
                inrm = e1.cross(e2).normalized()
                ipos = ro + t * rd
                itex = V(u, v)

    return t, id, ipos, inrm, itex


@ti.func
def union_intersect(ret1, ret2):
    ret = [ti.expr_init(x) for x in ret1]
    if ret2[0] < ret[0]:
        for x, y in ti.static(zip(ret, ret2)):
            x.assign(y)
    return ret


@ti.data_oriented
class BRDF:
    def __init__(self, **kwargs):
        @ti.materialize_callback
        def _():
            for k, v in kwargs.items():
                getattr(self, k)[None] = v

    def brdf(self, idir, odir):
        raise NotImplementedError

    @ti.func
    def rand_odir(self, idir):
        return 1, spherical(ti.random(), ti.random())

    @ti.func
    def bounce(self, dir, nrm):
        axes = tangentspace(nrm)
        idir = axes.transpose() @ -dir
        fac, odir = self.rand_odir(idir)
        clr = self.brdf(idir, odir)
        return axes @ odir, clr * fac


class CookTorranceBRDF(BRDF):
    def __init__(self, **kwargs):
        self.roughness = ti.field(float, ())
        self.metallic = ti.field(float, ())
        self.specular = ti.field(float, ())
        self.basecolor = ti.Vector.field(3, float, ())

        super().__init__(**kwargs)

    @ti.func
    def ischlick(self, cost):
        k = (self.roughness[None] + 1)**2 / 8
        return k + (1 - k) * cost

    @ti.func
    def fresnel(self, f0, HoV):
        return f0 + (1 - f0) * (1 - HoV)**5

    @ti.func
    def brdf(self, idir, odir):
        roughness = self.roughness[None]
        metallic = self.metallic[None]
        specular = self.specular[None]
        basecolor = self.basecolor[None]
        half = (idir + odir).normalized()
        NoH = max(EPS, half.z)
        NoL = max(EPS, idir.z)
        NoV = max(EPS, odir.z)
        HoV = min(1 - EPS, max(EPS, half.dot(odir)))
        ndf = roughness**2 / (NoH**2 * (roughness**2 - 1) + 1)**2
        vdf = 0.25 / (self.ischlick(NoL) * self.ischlick(NoV))
        f0 = metallic * basecolor + (1 - metallic) * 0.16 * specular**2
        ks, kd = f0, (1 - f0) * (1 - metallic)
        fdf = self.fresnel(f0, NoV)
        return kd * basecolor + ks * fdf * vdf * ndf / ti.pi


class DiffuseBRDF(BRDF):
    def __init__(self, **kwargs):
        self.color = ti.Vector.field(3, float, ())

        super().__init__(**kwargs)

    @ti.func
    def brdf(self, idir, odir):
        return self.color[None]


class SpecularBRDF(BRDF):
    def __init__(self, **kwargs):
        self.color = ti.Vector.field(3, float, ())

        super().__init__(**kwargs)

    @ti.func
    def rand_odir(self, idir):
        odir = reflect(-idir, V(0., 0., 1.))
        return odir

    @ti.func
    def brdf(self, idir, odir):
        return self.color[None]


class BlinnPhongBRDF(BRDF):
    def __init__(self, **kwargs):
        self.shineness = ti.field(float, ())

        super().__init__(**kwargs)

    @ti.func
    def brdf(self, idir, odir):
        shineness = self.shineness[None]
        half = (odir + idir).normalized()
        return (shineness + 8) / 8 * pow(max(0, half.z), shineness)


@ti.data_oriented
class PathEngine:
    def __init__(self, res=(512, 512), nrays=32, ntimes=1, nsteps=5):
        self.res = tovector(res if hasattr(res, '__getitem__') else (res, res))
        self.nrays = V(self.res.x, self.res.y, nrays)
        self.ntimes = ntimes
        self.nsteps = nsteps

        self.count = ti.field(int, self.res)
        self.screen = ti.Vector.field(3, float, self.res)
        self.ray_org = ti.Vector.field(3, float, self.nrays)
        self.ray_dir = ti.Vector.field(3, float, self.nrays)
        self.ray_color = ti.Vector.field(3, float, self.nrays)

    @ti.func
    def generate_ray(self, I):
        coor = I / self.res * 2 - 1
        #org = V23(coor, -1.)
        #dir = V(0., 0., 1.)
        org = V(0., 0., -1.)
        dir = V23(coor, 1.).normalized()
        return org, dir

    @ti.kernel
    def generate_rays(self):
        for r in ti.grouped(self.ray_org):
            I = r.xy + V(ti.random(), ti.random())
            org, dir = self.generate_ray(I)
            self.ray_org[r] = org
            self.ray_dir[r] = dir
            self.ray_color[r] = V(1., 1., 1.)

    @ti.func
    def intersect(self, org, dir):
        ret_1 = triangle_intersect(1,
                V(-.5, -.5, 0.), V(+.5, -.5, 0.), V(0., +.5, 0.),
                org, dir)
        ret_2 = triangle_intersect(2,
                V(-.5, -.5, -.5), V(+.5, -.5, -.5), V(0., -.5, +.5),
                org, dir)
        return union_intersect(ret_1, ret_2)

    @ti.func
    def bounce_ray(self, org, dir, i_id, i_pos, i_nrm, i_tex):
        org = i_pos + i_nrm * EPS
        color = V(0., 0., 0.)
        if i_id == 1:
            dir *= 0
            color = V(4., 4., 4.)
        elif i_id == 2:
            dir, color = mat_diffuse.bounce(dir, i_nrm)
        elif i_id == 3:
            dir, color = mat_ground.bounce(dir, i_nrm)
        elif i_id == 4:
            dir, color = mat_glossy.bounce(dir, i_nrm)
        return color, org, dir

    @ti.kernel
    def step_rays(self):
        for r in ti.grouped(self.ray_org):
            if all(self.ray_dir[r] == 0):
                continue

            org = self.ray_org[r]
            dir = self.ray_dir[r]
            t, i_id, i_pos, i_nrm, i_tex = self.intersect(org, dir)
            if t >= INF:
                self.ray_color[r] *= 0
                self.ray_dir[r] *= 0
            else:
                color, org, dir = self.bounce_ray(org, dir, i_id, i_pos, i_nrm, i_tex)
                self.ray_color[r] *= color
                self.ray_org[r] = org
                self.ray_dir[r] = dir

    @ti.kernel
    def update_screen(self):
        for I in ti.grouped(self.screen):
            for samp in range(self.nrays.z):
                r = V23(I, samp)
                color = self.ray_color[r]
                count = self.count[I]
                self.screen[I] *= count / (count + 1)
                self.screen[I] += color / (count + 1)
                self.count[I] += 1

    def main(self):
        for i in range(self.ntimes):
            with ezprof.scope('step'):
                self.generate_rays()
                for j in range(self.nsteps):
                    self.step_rays()
                self.update_screen()
        ezprof.show()
        img = aces_tonemap(ti.imresize(self.screen, 512))
        ti.imshow(img)#; ti.imwrite(img, '/tmp/out.png')


if __name__ == '__main__':
    ti.init(ti.opengl)

    mat_diffuse = CookTorranceBRDF(roughness=0.8,
            basecolor=(1, 1, 1),
            metallic=0.0,
            specular=0.5)
    mat_glossy = CookTorranceBRDF(roughness=0.2,
            basecolor=(1, 1, 1),
            metallic=0.9,
            specular=0.5)
    mat_ground = CookTorranceBRDF(roughness=0.4,
            basecolor=(1, 0, 0),
            metallic=0.0,
            specular=1.0)

    engine = PathEngine()
    engine.main()
