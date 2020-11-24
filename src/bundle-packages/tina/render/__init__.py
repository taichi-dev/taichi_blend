from .. import *


class IMatrix(INode):
    def __init__(self):
        self.matrix = Field(C.float(4, 4)[None])

        @ti.materialize_callback
        @ti.kernel
        def init_matrix():
            self.matrix[None] = ti.Matrix.identity(float, 4)

    @ti.func
    def get_matrix(self):
        return self.matrix[None]

    @ti.func
    def apply(self, pos, wei):
        mat = self.get_matrix()
        res = ti.Vector([mat[i, 3] for i in range(3)]) * wei
        for i, j in ti.static(ti.ndrange(3, 3)):
            res[i] += mat[i, j] * pos[j]
        rew = mat[3, 3] * wei
        for i in ti.static(range(3)):
            rew += mat[3, i] * pos[i]
        return res, rew

    def to_numpy(self):
        return self.matrix[None].value.to_numpy()


from . import viewport_transform
from . import particle_rasterize
from . import triangle_rasterize
from . import apply_transform
from . import matrix_inverse
from . import matrix_multiply
from . import face_vertices
from . import simple_shader
from . import clear_buffer
