'''
linear BVH tree implementation that can be constructed in real-time

https://developer.nvidia.com/blog/thinking-parallel-part-iii-tree-construction-gpu/
'''

from tina.common import *
from tina.model import *
from tina.stack import *


@ti.pyfunc
def expandBits(v):
    v = (v * 0x00010001) & clamp_unsigned(0xFF0000FF)
    v = (v * 0x00000101) & clamp_unsigned(0x0F00F00F)
    v = (v * 0x00000011) & clamp_unsigned(0xC30C30C3)
    v = (v * 0x00000005) & clamp_unsigned(0x49249249)
    '''
    v = (v | (v << 16)) & 0x030000FF
    v = (v | (v <<  8)) & 0x0300F00F
    v = (v | (v <<  4)) & 0x030C30C3
    v = (v | (v <<  2)) & 0x09249249
    '''
    return v


@ti.pyfunc
def morton3D(v):
    w = expandBits(clamp(ifloor(v * 1024), 0, 1023))
    return w.dot(V(4, 2, 1))


@ti.pyfunc
def clz(x):
    r = 0
    while True:
        f = x >> (31 - r)
        if f == 1 or r == 31:
            r += 1
            break
        r += 1
    return r


@ti.data_oriented
class LinearBVH:
    def __init__(self, n=2**22):  # 32 MB
        self.bmin = ti.Vector.field(3, float, n)
        self.bmax = ti.Vector.field(3, float, n)
        self.bready = ti.field(int, n)

        self.child = ti.Vector.field(2, int, n)
        self.leaf = ti.field(int, n)

        self.mc = ti.field(int, n)
        self.id = ti.field(int, n)

        self.n = ti.field(int, ())


    @ti.func
    def findSplit(self, l, r):
        m = 0

        lc, rc = self.mc[l], self.mc[r]
        if lc == rc:
            m = (l + r) >> 1

        else:
            cp = clz(lc ^ rc)

            m = l
            s = r - l

            while True:
                s += 1
                s >>= 1
                n = m + s

                if n < r:
                    nc = self.mc[n]
                    sp = clz(lc ^ nc)
                    if sp > cp:
                        m = n

                if s <= 1:
                    break

        return m


    @ti.func
    def determineRange(self, n, i):
        l, r = 0, n - 1

        if i != 0:
            ic = self.mc[i]
            lc = self.mc[i - 1]
            rc = self.mc[i + 1]

            if lc == ic == rc:
                l = i
                while i < n - 1:
                    i += 1
                    if i >= n - 1:
                        break
                    if self.mc[i] != self.mc[i + 1]:
                        break
                r = i

            else:
                ld = clz(ic ^ lc)
                rd = clz(ic ^ rc)

                d = -1
                if rd > ld:
                    d = 1
                delta_min = min(ld, rd)
                lmax = 2
                delta = -1
                itmp = i + d * lmax
                if 0 <= itmp < n:
                    delta = clz(ic ^ self.mc[itmp])
                while delta > delta_min:
                    lmax <<= 1
                    itmp = i + d * lmax
                    delta = -1
                    if 0 <= itmp < n:
                        delta = clz(ic ^ self.mc[itmp])
                s = 0
                t = lmax >> 1
                while t > 0:
                    itmp = i + (s + t) * d
                    delta = -1
                    if 0 <= itmp < n:
                        delta = clz(ic ^ self.mc[itmp])
                    if delta > delta_min:
                        s += t
                    t >>= 1

                l, r = i, i + s * d
                if d < 0:
                    l, r = r, l

        return l, r


    @ti.func
    def getVertices(self, i):
        face = ModelPool().get_face(i)
        v0, v1, v2 = face.v0, face.v1, face.v2
        return v0, v1, v2


    @ti.func
    def getBoundingBox(self, i):
        v0, v1, v2 = self.getVertices(i)
        return min(v0, v1, v2), max(v0, v1, v2)


    @ti.func
    def getCenter(self, i):
        v0, v1, v2 = self.getVertices(i)
        center = (v0 + v1 + v2) / 3
        return center


    @ti.kernel
    def genMortonCodes(self):
        n = ModelPool().nfaces[None]
        self.n[None] = n

        bmin, bmax = V3(inf), V3(-inf)
        for i in range(n):
            center = self.getCenter(i)
            ti.atomic_max(bmax, center)
            ti.atomic_min(bmin, center)

        for i in range(n):
            center = self.getCenter(i)
            coord = (center - bmin) / (bmax - bmin)
            self.mc[i] = morton3D(coord)
            self.id[i] = i


    @ti.kernel
    def exportMortonCodes(self, arr: ti.ext_arr()):
        n = self.n[None]

        for i in range(n):
            arr[i, 0] = self.mc[i]
            arr[i, 1] = self.id[i]


    @ti.kernel
    def importMortonCodes(self, arr: ti.ext_arr()):
        n = self.n[None]

        for i in range(n):
            self.mc[i] = arr[i, 0]
            self.id[i] = arr[i, 1]


    def sortMortonCodes(self):
        arr = np.empty((self.n[None], 2), dtype=np.int32)
        self.exportMortonCodes(arr)
        sort = np.argsort(arr[:, 0])
        self.importMortonCodes(arr[sort])


    @ti.kernel
    def genHierarchy(self):
        n = self.n[None]

        for i in range(n):
            self.leaf[i] = self.id[i]

        for i in range(n - 1):
            l, r = self.determineRange(n, i)
            split = self.findSplit(l, r)

            lhs = split
            if lhs != l:
                lhs += n

            rhs = split + 1
            if rhs != r:
                rhs += n

            self.child[i][0] = lhs
            self.child[i][1] = rhs


    @ti.func
    def getNodeBoundingBox(self, n, i):
        bready = 0
        bmin, bmax = V3(0.0), V3(0.0)

        if i < n:  # leaf node
            bmin, bmax = self.getBoundingBox(self.leaf[i])
            bready = 1

        else:      # internal node
            i -= n
            bmin, bmax = self.bmin[i], self.bmax[i]
            bready = self.bready[i]

        return bready, bmin, bmax


    def genAABBs(self):
        count = 1
        self.clearAABBStates()
        print('[TinaBVH] running AABB first step...')
        while not self.genAABBSubstep():
            print('[TinaBVH] running AABB substep...')
            count += 1
            if count > 64:
                raise RuntimeError('AABB step never stop! hierarchy corrupted?')
        print('[TinaBVH] LBVH tree depth', count, '>=',
                int(np.ceil(np.log2(self.n[None]))))


    @ti.kernel
    def clearAABBStates(self):
        n = self.n[None]

        for i in range(n):
            self.bready[i] = 0


    @ti.kernel
    def genAABBSubstep(self) -> int:
        n = self.n[None]

        for i in range(n - 1):
            if self.bready[i]:
                continue

            bready1, bmin1, bmax1 = self.getNodeBoundingBox(n, self.child[i][0])
            bready2, bmin2, bmax2 = self.getNodeBoundingBox(n, self.child[i][1])

            if bready1 == 1 and bready2 == 1:
                bmin, bmax = min(bmin1, bmin2), max(bmax1, bmax2)

                self.bmin[i], self.bmax[i] = bmin, bmax
                self.bready[i] = 1

        all_ready = 1
        for i in range(n - 1):
            if self.bready[i] == 0:
                all_ready = 0

        return all_ready


    def build(self):
        print('[TinaBVH] building LBVH tree...')
        self.genMortonCodes()
        print('[TinaBVH] sorting morton codes...')
        self.sortMortonCodes()
        print('[TinaBVH] generating hierarchy...')
        self.genHierarchy()
        self.genAABBs()
        print('[TinaBVH] building LBVH tree done')


    @ti.func
    def element_intersect(self, index, ray):
        return ModelPool().get_face(index).intersect(ray)


    @ti.func
    def intersect(self, ray, avoid):
        n = self.n[None]

        stack = Stack().get()
        stack.clear()
        stack.push(n)

        ret = namespace(hit=0, depth=inf, index=-1, uv=V(0., 0.))

        ntimes = 0
        while ntimes < n and stack.size() != 0:
            curr = stack.pop()

            if curr < n:
                index = self.leaf[curr]
                if index != avoid:
                    hit = self.element_intersect(index, ray)
                    if hit.hit != 0 and hit.depth < ret.depth:
                        ret.depth = hit.depth
                        ret.index = index
                        ret.uv = hit.uv
                        ret.hit = 1
                continue

            i = curr - n
            bbox = Box(self.bmin[i], self.bmax[i])
            if bbox.intersect(ray).hit == 0:
                continue

            ntimes += 1
            stack.push(self.child[i][0])
            stack.push(self.child[i][1])

        return ret


@ti.data_oriented
class BVHTree(LinearBVH, metaclass=Singleton):
    pass


def export_boxes(path, bmins, bmaxs):
    with open(path, 'w') as f:
        for bmin, bmax in zip(bmins, bmaxs):
            print(*bmin, *bmax, file=f)


if __name__ == '__main__':
    ModelPool()
    bvh = LinearBVH(2**16)

    from tina.tools.readgltf import readgltf
    ModelPool().load('assets/cube.obj')
    bvh.genMortonCodes()
    bvh.sortMortonCodes()
    bvh.genHierarchy()
    bvh.genAABBs()

    n = bvh.n[None]
    leaf = bvh.leaf.to_numpy()[:n]
    child = bvh.child.to_numpy()[:n - 1]
    bmin = bvh.bmin.to_numpy()[:n - 1]
    bmax = bvh.bmax.to_numpy()[:n - 1]

    export_boxes('/tmp/boxes.txt', bmin, bmax)

    exit(1)
