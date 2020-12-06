from utils import *
import ezprof
ti.init(ti.opengl)


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
    return i_t, s_id, i_pos, i_nrm


@ti.func
def union_intersect(ret1, ret2):
    t, id, pos, nrm = ret1
    if ret2[0] < t:
        t, id, pos, nrm = ret2
    return t, id, pos, nrm


@ti.func
def spherical(t, s):
    unit = V(ti.cos(t * ti.tau), ti.sin(t * ti.tau))
    dir = V23(ti.sqrt(1 - s**2) * unit, s)
    return dir


@ti.func
def unspherical(dir):
    t = ti.atan2(dir.y, dir.x) / ti.tau
    return t, dir.z


@ti.func
def tangentspace(nrm):
    up = V(0., 1., 0.)
    bitan = nrm.cross(up).normalized()
    tan = bitan.cross(nrm)
    return ti.Matrix.cols([tan, bitan, nrm])


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


@ti.func
def expensive(x, t, k):
    u = ti.tanh(x * k - t)
    n1 = ti.tanh(t)
    n2 = ti.tanh(k - t)
    pdf = (1 - u**2) / (n1 + n2) * k
    cdf = (u + n1) / (n2 + n1)
    return cdf, pdf


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
        ks, kd = f0, (1 - f0) * (1 - self.metallic)
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
#mat_glossy = SpecularBRDF(color=(1, 1, 1))


@ti.data_oriented
class PathEngine:
    def __init__(self, res=(512, 512)):
        self.res = tovector(res)

        self.nrays = V(self.res.x, self.res.y, 1)

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
        ret1 = sphere_intersect(1, V(-.5, 0., 0.), .4, org, dir)
        ret2 = sphere_intersect(2, V(+.5, 0., 0.), .4, org, dir)
        ret3 = sphere_intersect(3, V(0, -1e2-.5, 0.), 1e2, org, dir)
        ret4 = sphere_intersect(4, V(0., -.35, -.25), .15, org, dir)
        ret = union_intersect(ret1, union_intersect(ret2, union_intersect(ret3, ret4)))
        return ret

    @ti.func
    def bounce_ray(self, org, dir, i_id, i_pos, i_nrm):
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
            t, i_id, i_pos, i_nrm = self.intersect(org, dir)
            if t >= INF:
                self.ray_color[r] *= 0
                self.ray_dir[r] *= 0
            else:
                color, org, dir = self.bounce_ray(org, dir, i_id, i_pos, i_nrm)
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
        for i in range(512):
            with ezprof.scope('step'):
                self.generate_rays()
                for j in range(5):
                    self.step_rays()
                self.update_screen()
        ezprof.show()
        img = aces_tonemap(ti.imresize(self.screen, 512))
        ti.imshow(img)#; ti.imwrite(img, '/tmp/out.png')


if __name__ == '__main__':
    PathEngine().main()
