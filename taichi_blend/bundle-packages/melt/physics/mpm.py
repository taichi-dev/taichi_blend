from . import *


@ti.data_oriented
class MPMSolver:
    WATER = 0
    JELLY = 1
    SNOW = 2
    SAND = 3

    def __init__(self, res, size=1, dt_scale=1, E_scale=1, gravity=(0, 9.8, 0)):
        self.res = tovector(res)
        self.dim = len(self.res)
        assert self.dim in [2, 3]
        self.dx = size / self.res.x
        self.dt = 2e-2 * self.dx / size * dt_scale
        self.steps = int(1 / (120 * self.dt))

        self.p_rho = 1e3
        self.p_vol = self.dx**self.dim
        self.p_mass = self.p_vol * self.p_rho
        self.gravity = tovector(gravity[:self.dim])
        self.E = 1e6 * size * E_scale
        self.nu = 0.2

        self.mu_0 = self.E / (2 * (1 + self.nu))
        self.lambda_0 = self.E * self.nu / ((1 + self.nu) * (1 - 2 * self.nu))
        sin_phi = ti.sin(np.radians(45))
        self.alpha = ti.sqrt(2 / 3) * 2 * sin_phi / (3 - sin_phi)

        self.num = ti.field(int, ())
        self.x = ti.Vector.field(self.dim, float)
        self.v = ti.Vector.field(self.dim, float)
        self.C = ti.Matrix.field(self.dim, self.dim, float)
        self.F = ti.Matrix.field(self.dim, self.dim, float)
        self.material = ti.field(int)
        self.Jp = ti.field(float)

        indices = ti.ij if self.dim == 2 else ti.ijk

        grid_size = 1024
        grid_block_size = 128
        leaf_block_size = 16 if self.dim == 2 else 8
        self.grid = ti.root.pointer(indices, grid_size // grid_block_size)
        block = self.grid.pointer(indices, grid_block_size // leaf_block_size)

        self.offset = (-grid_size // 2,) * self.dim
        def block_component(c):
            block.dense(indices, leaf_block_size).place(c, offset=self.offset)

        self.grid_v = ti.Vector.field(self.dim, float)
        self.grid_m = ti.field(float)

        block_component(self.grid_m)
        for v in self.grid_v.entries:
            block_component(v)

        self.pid = ti.field(int)
        block.dynamic(ti.indices(self.dim), 2**20,
                chunk_size=leaf_block_size**self.dim * 8).place(
                        self.pid, offset=self.offset + (0,))

        max_num_particles = 2**27
        self.particle = ti.root.dynamic(ti.i, max_num_particles, 2**20)
        for c in [self.x, self.v, self.C, self.F, self.material, self.Jp]:
            self.particle.place(c)
        self.particle_num = ti.field(int, ())

    @ti.kernel
    def emit(self, material: int, pars: ti.template()):
        for i in ti.smart(pars):
            pos = pars[i]
            n = ti.atomic_add(self.num[None], 1)
            vel = ti.Vector.zero(float, self.dim)
            self.emit_particle(n, pos, vel, material)

    @ti.func
    def emit_particle(self, i, pos, vel, material):
        self.x[i] = pos
        self.v[i] = vel
        self.F[i] = ti.Matrix.identity(float, self.dim)
        self.C[i] = ti.Matrix.zero(float, self.dim, self.dim)
        self.material[i] = material
        if material == self.SAND:
            self.Jp[i] = 0
        else:
            self.Jp[i] = 1

    def stencil_range(self):
        return ti.ndrange(*(3,) * self.dim)

    @ti.kernel
    def build_pid(self):
        ti.block_dim(64)
        for p in self.particle:
            base = int(ti.floor(self.x[p] / self.dx - 0.5))
            ti.append(self.pid.parent(), base - tovector(self.offset), p)

    @ti.kernel
    def p2g(self):
        ti.no_activate(self.particle)
        ti.block_dim(256)
        ti.block_local(self.grid_v)
        ti.block_local(self.grid_m)
        for I in ti.grouped(self.pid):
            p = self.pid[I]
            Xp = self.x[p] / self.dx
            base = int(ti.floor(Xp - 0.5))
            fx = Xp - base
            w = [0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2, 0.5 * (fx - 0.5)**2]
            self.F[p] = (ti.Matrix.identity(float, self.dim) + self.dt * self.C[p]) @ self.F[p]
            h = ti.exp(10 * (1 - self.Jp[p]))
            if self.material[p] == self.JELLY:
                h = 0.3
            mu, la = self.mu_0 * h, self.lambda_0 * h
            if self.material[p] == self.WATER:
                mu = 0.0
            U, sig, V = ti.svd(self.F[p])
            J = 1.0
            if self.material[p] != self.SAND:
                for d in ti.static(range(self.dim)):
                    new_sig = sig[d, d]
                    if self.material[p] == self.SNOW:
                        new_sig = min(max(sig[d, d], 1 - 2.5e-2), 1 + 4.5e-3)
                    self.Jp[p] *= sig[d, d] / new_sig
                    sig[d, d] = new_sig
                    J *= new_sig
            if self.material[p] == self.WATER:
                self.F[p] = ti.Matrix.identity(float, self.dim) * J**(1 / self.dim)
            elif self.material[p] == self.SNOW:
                self.F[p] = U @ sig @ V.transpose()
            stress = ti.Matrix.identity(float, self.dim)
            if self.material[p] != self.SAND:
                stress = 2 * mu * (self.F[p] - U @ V.transpose()) @ self.F[p].transpose()
                stress += ti.Matrix.identity(float, self.dim) * la * J * (J - 1)
            else:
                sig = self.sand_projection(sig, p)
                self.F[p] = U @ sig @ V.transpose()
                log_sig_sum = 0.0
                center = ti.Matrix.zero(float, self.dim, self.dim)
                for i in ti.static(range(self.dim)):
                    log_sig = ti.log(sig[i, i])
                    center[i, i] = 2.0 * self.mu_0 * log_sig / sig[i, i]
                    log_sig_sum += log_sig
                for i in ti.static(range(self.dim)):
                    center[i, i] += self.lambda_0 * log_sig_sum / sig[i, i]
                stress = U @ center @ V.transpose() @ self.F[p].transpose()

            stress = (-self.dt * self.p_vol * 4 / self.dx**2) * stress
            affine = stress + self.p_mass * self.C[p]
            for offset in ti.grouped(ti.ndrange(*(3,) * self.dim)):
                dpos = (offset - fx) * self.dx
                weight = 1.0
                for i in ti.static(range(self.dim)):
                    weight *= list_subscript(w, offset[i])[i]
                self.grid_v[base + offset] += weight * (self.p_mass * self.v[p] + affine @ dpos)
                self.grid_m[base + offset] += weight * self.p_mass

    @ti.kernel
    def grid_normalize(self):
        for I in ti.grouped(self.grid_m):
            if self.grid_m[I] > 0:
                self.grid_v[I] /= self.grid_m[I]
            self.grid_v[I] -= self.dt * self.gravity

    @ti.kernel
    def grid_boundary(self):
        for I in ti.grouped(self.grid_m):
            cond1 = I < -self.res and self.grid_v[I] < 0
            cond2 = I > self.res and self.grid_v[I] > 0
            self.grid_v[I] = 0 if cond1 or cond2 else self.grid_v[I]

    @ti.kernel
    def g2p(self):
        ti.no_activate(self.particle)
        ti.block_dim(256)
        ti.block_local(self.grid_v)
        for I in ti.grouped(self.pid):
            p = self.pid[I]
            Xp = self.x[p] / self.dx
            base = int(ti.floor(Xp - 0.5))
            fx = Xp - base
            w = [0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2, 0.5 * (fx - 0.5)**2]
            new_v = ti.Vector.zero(float, self.dim)
            new_C = ti.Matrix.zero(float, self.dim, self.dim)
            for offset in ti.grouped(ti.ndrange(*(3,) * self.dim)):
                dpos = offset - fx
                weight = 1.0
                for i in ti.static(range(self.dim)):
                    weight *= list_subscript(w, offset[i])[i]
                g_v = self.grid_v[base + offset]
                new_v += weight * g_v
                new_C += 4 * weight * g_v.outer_product(dpos) / self.dx
            self.v[p] = new_v
            self.C[p] = new_C
            self.x[p] += self.dt * self.v[p]

    @ti.func
    def sand_projection(self, sigma, p):
        sigma_out = ti.Matrix.zero(ti.f32, self.dim, self.dim)
        epsilon = ti.Vector.zero(ti.f32, self.dim)
        for i in ti.static(range(self.dim)):
            epsilon[i] = ti.log(max(abs(sigma[i, i]), 1e-4))
            sigma_out[i, i] = 1
        tr = epsilon.sum() + self.Jp[p]
        epsilon_hat = epsilon - tr / self.dim
        epsilon_hat_norm = epsilon_hat.norm() + 1e-20
        if tr >= 0.0:
            self.Jp[p] = tr
        else:
            self.Jp[p] = 0.0
            delta_gamma = epsilon_hat_norm + (
                self.dim * self.lambda_0 +
                2 * self.mu_0) / (2 * self.mu_0) * tr * self.alpha
            for i in ti.static(range(self.dim)):
                sigma_out[i, i] = ti.exp(epsilon[i] - max(0, delta_gamma) /
                                         epsilon_hat_norm * epsilon_hat[i])

        return sigma_out

    @ti.kernel
    def get_num_particles(self) -> int:
        return ti.length(self.particle, [])

    @ti.kernel
    def _get_particle_pos(self, out: ti.ext_arr()):
        for i in range(out.shape[0]):
            for k in ti.static(range(self.dim)):
                out[i, k] = self.x[i][k]

    def get_particle_pos(self):
        num = self.get_num_particles()
        out = np.empty((num, self.dim), dtype=np.float32)
        self._get_particle_pos(out)
        return out

    def step(self):
        for s in range(self.steps):
            self.grid.deactivate_all()
            self.build_pid()
            self.p2g()
            self.grid_normalize()
            self.grid_boundary()
            self.g2p()


@A.register
class MPMDomain:
    '''
    Name: mpm_domain
    Category: physics
    Inputs: res:i3 gravity:c3
    Output: pos:vf% vel:vf% mat:f% update:t% domain:a
    '''
    def __init__(self, res, gravity=(0, 0, 9.8)):
        self.mpm = MPMSolver(res, gravity=gravity)
        self.update = self._RunProxy(self.mpm.step)
        self.pos = self._FieldProxy(self.mpm.x, C.float(3), self.mpm.get_num_particles)
        self.vel = self._FieldProxy(self.mpm.v, C.float(3), self.mpm.get_num_particles)
        self.mat = self._FieldProxy(self.mpm.material, C.int(), self.mpm.get_num_particles)

    class _RunProxy(IRun):
        def __init__(self, func):
            self.func = func

        def run(self):
            self.func()

    class _FieldProxy(Field):
        def __init__(self, field, meta, getlen):
            self.meta = meta
            self.core = field
            self.get_length = getlen


@A.register
class MPMEmitter(IRun):
    '''
    Name: mpm_emitter
    Category: physics
    Inputs: domain:a material:mtr sample:vf
    Output: emit:t
    '''
    def __init__(self, domain, material, sample):
        assert isinstance(sample, IField)
        self.domain = domain
        self.material = 'water jelly snow sand'.split().index(material)
        self.sample = sample

    def run(self):
        self.domain.mpm.emit(self.material, self.sample)


@A.register
class FilterMaterial(IField):
    '''
    Name: filter_material
    Category: converter
    Inputs: pos:vf mat:f material:mtr
    Output: pos:vf
    '''
    def __init__(self, pos, mat, material):
        assert isinstance(pos, IField)
        self.pos = pos
        self.mat = mat
        self.material = 'water jelly snow sand'.split().index(material)

    @ti.func
    def __iter__(self):
        for I in ti.smart(self.pos):
            if self.mat[I] == self.material:
                yield I

    @ti.func
    def _subscript(self, I):
        return self.pos[I]
