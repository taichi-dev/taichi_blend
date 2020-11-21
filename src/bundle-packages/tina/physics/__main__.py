from . import *
from .mpm88 import MPMSolver


class VisualMPMSolver(MPMSolver):
    def T(self, a):
        if self.dim == 2:
            return a

        import numpy as np

        phi, theta = np.radians(28), np.radians(32)

        a = a - 0.5
        x, y, z = a[:, 0], a[:, 1], a[:, 2]
        c, s = np.cos(phi), np.sin(phi)
        C, S = np.cos(theta), np.sin(theta)
        x, z = x * c + z * s, z * c - x * s
        u, v = x, y * C + z * S
        return np.array([u, v]).swapaxes(0, 1) + 0.5


    @ti.kernel
    def init(self):
        for i in range(self.n_particles):
            self.x[i] = ti.Vector([ti.random() for i in range(self.dim)]) * 0.4 + 0.15


    def main(self):
        print(f'Running with {self.n_particles} parcticles...')
        self.init()
        with ti.GUI(f'MPM{self.dim}D', background_color=0x112F41) as gui:
            while gui.running and not gui.get_event(gui.ESCAPE):
                self.run()
                pos = self.x.to_numpy()
                gui.circles(self.T(pos), radius=1.5, color=0x66ccff)
                gui.show()


if __name__ == '__main__':
    ti.init(arch=ti.gpu)

    solver = VisualMPMSolver(3, 32)
    solver.main()
