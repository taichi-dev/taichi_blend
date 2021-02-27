'''
camera that generate rays from a given 4x4 perspective matrix
'''

from tina.geometries import *


@ti.data_oriented
class Camera(metaclass=Singleton):
    def __init__(self):
        self._V2W = ti.field(float, (4, 4))
        self._W2V = ti.field(float, (4, 4))

        @ti.materialize_callback
        def init_camera():
            from tina.tools.matrix import ortho, lookat
            self.set_perspective(ortho() @ lookat())

    def set_perspective(self, pers):
        invpers = np.linalg.inv(pers)
        self._V2W.from_numpy(invpers)
        self._W2V.from_numpy(pers)

    @property
    @ti.pyfunc
    def V2W(self):
        return ti.Matrix([[self._V2W[i, j] for j in range(4)] for i in range(4)])

    @property
    @ti.pyfunc
    def W2V(self):
        return ti.Matrix([[self._W2V[i, j] for j in range(4)] for i in range(4)])

    @ti.func
    def generate(self, x, y):
        ro = V43(self.V2W @ V(x, y, -1.0, 1.0))
        ro1 = V43(self.V2W @ V(x, y, 1.0, 1.0))
        rd = (ro1 - ro).normalized()
        return Ray(ro, rd)
