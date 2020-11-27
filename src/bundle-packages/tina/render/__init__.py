from .. import *


@ti.func
def mapply(mat, pos, wei):
    res = ti.Vector([mat[i, 3] for i in range(3)]) * wei
    for i, j in ti.static(ti.ndrange(3, 3)):
        res[i] += mat[i, j] * pos[j]
    rew = mat[3, 3] * wei
    for i in ti.static(range(3)):
        rew += mat[3, i] * pos[i]
    return res, rew


class IMatrix(INode):
    def __init__(self):
        self.matrix = Field(C.float(4, 4)[None])
        self.inv_matrix = Field(C.float(4, 4)[None])

        @ti.materialize_callback
        @ti.kernel
        def init_matrix():
            self.matrix[None] = ti.Matrix.identity(float, 4)
            self.inv_matrix[None] = ti.Matrix.identity(float, 4)

    @ti.func
    def get_matrix(self):
        return self.matrix[None]

    @ti.func
    def get_inv_matrix(self):
        return self.inv_matrix[None]

    def from_numpy(self, mat):
        inv_mat = np.linalg.inv(mat)
        self.matrix[None] = mat.tolist()
        self.inv_matrix[None] = inv_mat.tolist()

    @ti.func
    def apply(self, pos, wei):
        return mapply(self.get_matrix(), pos, wei)

    @ti.func
    def unapply(self, pos, wei):
        return mapply(self.get_inv_matrix(), pos, wei)

    def to_numpy(self):  # use a kernel instead?
        return self.matrix[None].value.to_numpy()


from . import viewport_transform
from . import particle_rasterize
from . import triangle_rasterize
from . import face_flat_normal
from . import apply_transform
from . import matrix_multiply
from . import matrix_inverse
from . import face_vertices
from . import simple_shader
from . import clear_buffer
