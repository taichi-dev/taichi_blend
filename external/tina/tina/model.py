from tina.allocator import *
from tina.geometries import *


@ti.data_oriented
class ModelPool(metaclass=Singleton):
    is_taichi_class = True

    def __init__(self, size=2**20):
        self.nfaces = ti.field(int, ())
        self.vertices = ti.field(float, size * 8 * 3)
        self.mtlids = ti.field(int, size)

    @ti.func
    def subscript(self, i):
        return tovector([self.vertices[i * 8 + j] for j in range(8)])

    @ti.func
    def get_face(self, i):
        a0 = self[i * 3 + 0]
        a1 = self[i * 3 + 1]
        a2 = self[i * 3 + 2]
        v0 = V(a0[0], a0[1], a0[2])
        vn0 = V(a0[3], a0[4], a0[5])
        vt0 = V(a0[6], a0[7])
        v1 = V(a1[0], a1[1], a1[2])
        vn1 = V(a1[3], a1[4], a1[5])
        vt1 = V(a1[6], a1[7])
        v2 = V(a2[0], a2[1], a2[2])
        vn2 = V(a2[3], a2[4], a2[5])
        vt2 = V(a2[6], a2[7])
        mtlid = self.mtlids[i]
        return Face(v0, v1, v2, vn0, vn1, vn2, vt0, vt1, vt2, mtlid)

    @ti.kernel
    def _to_numpy(self, arr: ti.ext_arr(), mtlids: ti.ext_arr()):
        for i in range(self.nfaces[None]):
            mtlids[i] = self.mtlids[i]
        for i in range(self.nfaces[None] * 3):
            for k in ti.static(range(8)):
                arr[i, k] = self[i][k]

    def to_numpy(self, id):
        arr = np.empty((self.nfaces[None] * 3, 8), dtype=np.float32)
        mtlids = np.empty(self.nfaces[None], dtype=np.int32)
        self._to_numpy(arr, mtlids)
        return arr, mtlids

    @ti.kernel
    def from_numpy(self, arr: ti.ext_arr(), mtlids: ti.ext_arr()):
        self.nfaces[None] = mtlids.shape[0]
        for i in range(self.nfaces[None] * 3):
            for k in ti.static(range(8)):
                self[i][k] = arr[i, k]
        for i in range(self.nfaces[None]):
            self.mtlids[i] = mtlids[i]

    def load(self, arr, mtlids=None):
        if isinstance(arr, str):
            from tina.tools.readobj import readobj
            arr = readobj(arr)

        if isinstance(arr, dict):
            verts = arr['v'][arr['f'][:, :, 0]]
            norms = arr['vn'][arr['f'][:, :, 2]]
            coors = arr['vt'][arr['f'][:, :, 1]]
            verts = verts.reshape(arr['f'].shape[0] * 3, 3)
            norms = norms.reshape(arr['f'].shape[0] * 3, 3)
            coors = coors.reshape(arr['f'].shape[0] * 3, 2)
            arr = np.concatenate([verts, norms, coors], axis=1)

        if arr.dtype == np.float64:
            arr = arr.astype(np.float32)

        assert arr.shape[0] % 3 == 0
        if mtlids is None:
            mtlids = np.zeros(arr.shape[0] // 3, dtype=np.int32)
        else:
            assert mtlids.shape[0] == arr.shape[0] // 3
        assert mtlids.shape[0] < self.mtlids.shape[0], 'too many faces'

        self.from_numpy(arr, mtlids)
