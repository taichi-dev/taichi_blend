'''
simulated local integer stack for tree traversal in Taichi
'''

from tina.common import *
from tina.localarray import *


@ti.data_oriented
class GlobalStack(metaclass=Singleton):
    def __init__(self, N_mt=512*512, N_len=32):  # 32 MB
        if ti.cfg.arch == ti.cpu and ti.cfg.cpu_max_num_threads == 1 or ti.cfg.arch == ti.cc:
            N_mt = 1
        print('[TinaStack] Using', N_mt, 'global stacks')
        self.N_mt = N_mt
        self.N_len = N_len
        self.val = ti.field(int)
        self.blk1 = ti.root.dense(ti.i, N_mt)
        self.blk2 = self.blk1.dense(ti.j, N_len)
        self.blk2.place(self.val)
        self.len = ti.field(int, N_mt)

    def set(self, mtid):
        self._proxy = self.Proxy(self, mtid)

    def get(self):
        return self._proxy

    def unset(self):
        del self._proxy

    @ti.data_oriented
    class Proxy:
        def __init__(self, stack, mtid):
            self.stack = stack
            self.mtid = mtid

        def __getattr__(self, attr):
            return getattr(self.stack, attr)

        @ti.func
        def size(self):
            return self.len[self.mtid]

        @ti.func
        def clear(self):
            self.len[self.mtid] = 0

        @ti.func
        def push(self, val):
            l = self.len[self.mtid]
            self.val[self.mtid, l] = val
            self.len[self.mtid] = l + 1

        @ti.func
        def pop(self):
            l = self.len[self.mtid]
            val = self.val[self.mtid, l - 1]
            self.len[self.mtid] = l - 1
            return val


@ti.data_oriented
class LocalStack(metaclass=Singleton):
    def __init__(self, size=64):
        self.size = size

    def set(self, mtid):
        print('[TinaStack] Using local stack for OpenGL / CC')
        self._proxy = self.Proxy(self.size)

    def get(self):
        return self._proxy

    def unset(self):
        del self._proxy

    @ti.data_oriented
    class Proxy:
        def __init__(self, size):
            self.val = LocalArray(int, size)
            self.len = ti.expr_init(0)

        @ti.func
        def size(self):
            return self.len

        @ti.func
        def clear(self):
            self.len = 0

        @ti.func
        def push(self, val):
            self.val[self.len] = val
            self.len += 1

        @ti.func
        def pop(self):
            self.len -= 1
            val = self.val[self.len]
            return val


def Stack():
    if ti.cfg.arch in [ti.cc, ti.opengl]:
        return LocalStack()
    else:
        return GlobalStack()


@ti.func
def GSL(nx, ny, tnx=512, tny=512):
    '''grid stride loop'''
    for tx, ty in ti.ndrange(tnx, tny):
        x = tx
        while x < nx:
            y = ty
            while y < ny:
                Stack().set(tx * tny + ty)
                yield V(x, y)
                Stack().unset()
                y += tny
            x += tnx
