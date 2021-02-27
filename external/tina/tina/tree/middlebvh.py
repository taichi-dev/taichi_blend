'''
middle-point-split BVH tree implementation
'''

from tina.model import *
from tina.geometries import *
from tina.stack import *


@ti.data_oriented
class MiddleBVH:
    def __init__(self, size):
        self.size = size
        self.dir = ti.field(int, size)
        self.ind = ti.field(int, size)
        self.min = ti.Vector.field(3, float, size)
        self.max = ti.Vector.field(3, float, size)

    def build(self, pmin, pmax):
        assert len(pmin) == len(pmax)
        assert np.all(pmax >= pmin)
        data = lambda: None
        data.dir = self.dir.to_numpy()
        data.dir[:] = -1
        data.min = self.min.to_numpy()
        data.max = self.max.to_numpy()
        data.ind = self.ind.to_numpy()
        print('[TinaBVH] building middle-BVH tree...')
        self._build(data, pmin, pmax, np.arange(len(pmin)), 1)
        self._build_from_data(data.dir, data.min, data.max, data.ind)
        print('[TinaBVH] building middle-BVH tree done')

    @ti.kernel
    def _build_from_data(self,
            data_dir: ti.ext_arr(),
            data_min: ti.ext_arr(),
            data_max: ti.ext_arr(),
            data_ind: ti.ext_arr()):
        for i in range(self.dir.shape[0]):
            if data_dir[i] == -1:
                continue
            self.dir[i] = data_dir[i]
            for k in ti.static(range(3)):
                self.min[i][k] = data_min[i, k]
                self.max[i][k] = data_max[i, k]
            self.ind[i] = data_ind[i]

    def _build(self, data, pmin, pmax, pind, curr):
        assert curr < self.size, curr
        if not len(pind):
            return

        elif len(pind) <= 1:
            data.dir[curr] = 0
            data.ind[curr] = pind[0]
            data.min[curr] = pmin[0]
            data.max[curr] = pmax[0]
            return

        bmax = np.max(pmax, axis=0)
        bmin = np.min(pmin, axis=0)
        dir = np.argmax(bmax - bmin)
        sort = np.argsort(pmax[:, dir] + pmin[:, dir])
        mid = len(sort) // 2
        lsort = sort[:mid]
        rsort = sort[mid:]

        lmin, rmin = pmin[lsort], pmin[rsort]
        lmax, rmax = pmax[lsort], pmax[rsort]
        lind, rind = pind[lsort], pind[rsort]
        data.dir[curr] = 1 + dir
        data.ind[curr] = 0
        data.min[curr] = bmin
        data.max[curr] = bmax
        self._build(data, lmin, lmax, lind, curr * 2)
        self._build(data, rmin, rmax, rind, curr * 2 + 1)

    @ti.func
    def element_intersect(self, index, ray):
        return ModelPool().get_face(index).intersect(ray)

    @ti.func
    def process_leaf(self, ret: ti.template(), curr, ray, avoid):
        index = self.ind[curr]
        if index != avoid:
            hit = self.element_intersect(index, ray)
            if hit.hit != 0 and hit.depth < ret.depth:
                ret.depth = hit.depth
                ret.index = index
                ret.uv = hit.uv
                ret.hit = 1

    @ti.func
    def is_leaf(self, curr):
        return self.dir[curr] == 0

    @ti.func
    def getbox(self, curr):
        return Box(self.min[curr], self.max[curr])

    @ti.func
    def intersect(self, ray, avoid):
        stack = Stack().get()
        ntimes = 0
        stack.clear()
        stack.push(1)
        ret = namespace(hit=0, depth=inf, index=-1, uv=V(0., 0.))

        while ntimes < self.size and stack.size() != 0:
            curr = stack.pop()

            if self.is_leaf(curr):
                self.process_leaf(ret, curr, ray, avoid)
                continue

            if self.getbox(curr).intersect(ray).hit == 0:
                continue

            ntimes += 1
            stack.push(curr * 2)
            stack.push(curr * 2 + 1)

        return ret

    '''
    # https://developer.nvidia.com/blog/thinking-parallel-part-ii-tree-traversal-gpu/
    @ti.func
    def alternative_intersect(self, ray, avoid):
        stack = Stack().get()
        ntimes = 0
        ret = namespace(hit=0, depth=inf, index=-1, uv=V(0., 0.))

        stack.clear()
        stack.push(0)
        curr = 1  # root node

        while ntimes < self.size:
            left = curr * 2
            right = curr * 2 + 1

            hit_left = truth(self.getbox(left).intersect(ray).hit)
            hit_right = truth(self.getbox(right).intersect(ray).hit)

            if hit_left and truth(self.is_leaf(left)):
                self.process_leaf(ret, left, ray, avoid)

            if hit_right and truth(self.is_leaf(right)):
                self.process_leaf(ret, right, ray, avoid)

            go_left = truth(hit_left and not self.is_leaf(left))
            go_right = truth(hit_right and not self.is_leaf(right))

            if not go_left and not go_right:
                curr = stack.pop()
            else:
                curr = left if go_left else right
                if go_left and go_right:
                    stack.push(curr)

            if curr == 0:
                break

        return ret
    '''


@ti.data_oriented
class BVHTree(metaclass=Singleton):
    def __init__(self, size=2**20):
        self.core = MiddleBVH(size)

    @ti.kernel
    def _dump_face_bboxes(self, nfaces: int, pmin: ti.ext_arr(), pmax: ti.ext_arr()):
        for i in range(nfaces):
            bbox = ModelPool().get_face(i).getbbox()
            for k in ti.static(range(3)):
                pmin[i, k] = bbox.lo[k]
                pmax[i, k] = bbox.hi[k]

    def build(self):
        nfaces = ModelPool().nfaces[None]
        pmin = np.empty((nfaces, 3))
        pmax = np.empty((nfaces, 3))
        self._dump_face_bboxes(nfaces, pmin, pmax)
        self.core.build(pmin, pmax)

    @ti.func
    def intersect(self, ray, avoid):
        return self.core.intersect(ray, avoid)
