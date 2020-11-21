from . import *
from .mpm88 import MPMSolver


if __name__ == '__main__':
    ti.init(arch=ti.gpu)

    solver = MPMSolver(3, 32)
    solver.main()
