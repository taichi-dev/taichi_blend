'''
metropolis path integrator, great for rendering caustics
'''

from tina.engine.path import *


@ti.data_oriented
class MLTPathEngine(metaclass=Singleton):
    def __init__(self):
        self.nchains = nchains = 2**18
        self.ndims = ndims = 32

        self.X_old = ti.field(float, (nchains, ndims))
        self.X_new = ti.field(float, (nchains, ndims))
        self.L_old = ti.Vector.field(3, float, nchains)
        self.L_new = ti.Vector.field(3, float, nchains)
        self.accum = ti.field(float, nchains)

        self.LSP = ti.field(float, ())
        self.Sigma = ti.field(float, ())

        ti.materialize_callback(self.reset)

        @ti.materialize_callback
        def init_params():
            self.LSP[None] = 0.25
            self.Sigma[None] = 0.01

    @ti.kernel
    def reset(self):
        for i in range(self.nchains):
            self.L_old[i] = 0
            self.accum[i] = 1
            for j in range(self.ndims):
                self.X_old[i, j] = ti.random()

    @ti.kernel
    def _inc_film_count(self):
        '''
        for i, j in ti.ndrange(FilmTable().nx, FilmTable().ny):
            impo = 2.0 * self.nchains / (FilmTable().nx * FilmTable().ny)
            #impo = 0.0
            FilmTable()[0, i, j].w += impo
        '''

    @ti.func
    def splat(self, x, y, color):
        impo = 1.0
        #impo = 0.0
        i, j = ifloor(V(x * FilmTable().nx, y * FilmTable().ny))
        FilmTable()[0, i, j] += V34(color, impo)

    @ti.kernel
    def _render(self):
        for i in range(self.nchains):
            Stack().set(i)

            if ti.random() < self.LSP[None]:
                for j in range(self.ndims):
                    self.X_new[i, j] = ti.random()
            else:
                for j in range(self.ndims):
                    dX = self.Sigma[None] * normaldist(ti.random())
                    self.X_new[i, j] = (self.X_old[i, j] + dX) % 1

            rng = RNGProxy(self.X_new, i)
            ray = Camera().generate(rng.random() * 2 - 1, rng.random() * 2 - 1)
            clr = path_trace(ray, rng)
            self.L_new[i] = clr

            AL_new = Vavg(self.L_new[i]) + 1e-10
            AL_old = Vavg(self.L_old[i]) + 1e-10
            accept = min(1, AL_new / AL_old)
            L_new = self.L_new[i] * self.accum[i]
            self.splat(self.X_new[i, 0], self.X_new[i, 1], L_new)

            if ti.random() < accept:
                self.L_old[i] = self.L_new[i]
                for j in range(self.ndims):
                    self.X_old[i, j] = self.X_new[i, j]

            Stack().unset()

    def render(self):
        self._render()
        self._inc_film_count()
