from tina.common import *


@ti.pyfunc
def trace(rng):
    x, y = rng.random(), rng.random()
    return ((x - 0.5)**2 + (y - 0.34)**2) * 0.1


nres = V(64, 64)
film = ti.field(float, nres)
count = ti.field(float, nres)


@ti.func
def splat(X, L):
    I = clamp(ifloor(X * nres), 0, nres - 1)
    film[I] += L


LSP = 0.04
Sigma = 0.03

nchains = 1024
ndims = 2


X_old = ti.field(float, (nchains, ndims))
X_new = ti.field(float, (nchains, ndims))
L_old = ti.field(float, nchains)
L_new = ti.field(float, nchains)


@ti.data_oriented
class RNGProxy:
    def __init__(self, data, i):
        self.data = data
        self.i = ti.expr_init(i)
        self.j = ti.expr_init(0)

    @ti.func
    def random(self):
        ret = self.data[self.i, self.j]
        self.j += 1
        return ret


@ti.kernel
def render(first: int):
    for i in range(nchains):
        for j in range(ndims):
            X_new[i, j] = X_old[i, j]

        if first or ti.random() < LSP:
            for j in range(ndims):
                X_new[i, j] = ti.random()
        else:
            for j in range(ndims):
                dX = Sigma * normaldist(ti.random())
                X_new[i, j] = (X_old[i, j] + dX) % 1

        L_new[i] = trace(RNGProxy(X_new, i))

        AL_new = Vavg(L_new[i]) + 1e-10
        AL_old = Vavg(L_old[i]) + 1e-10
        accept = min(1, AL_new / AL_old)
        if accept > 0:
            splat(V(X_new[i, 0], X_new[i, 1]), accept * L_new[i] / AL_new)
        if not first:
            splat(V(X_old[i, 0], X_old[i, 1]), (1 - accept) * L_old[i] / AL_old)

        if accept > ti.random():
            L_old[i] = L_new[i]
            for j in range(ndims):
                X_old[i, j] = X_new[i, j]


gui = ti.GUI()

while gui.running and not gui.get_event(gui.ESCAPE):
    render(gui.frame <= 1)
    gui.set_image(ti.imresize(film.to_numpy() / (gui.frame + 1e-10), 512))
    gui.show()
