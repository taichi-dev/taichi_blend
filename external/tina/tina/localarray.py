from tina.common import *


@ti.data_oriented
class LocalArray:
    is_taichi_class = True
    uniqid = 0

    def __init__(self, dtype, size):
        assert ti.inside_kernel()
        self.uniqid += 1
        self.name = f'tmptls{self.uniqid}'
        self.size = size
        self.dtype = dtype
        dtype_str = ti.cook_dtype(dtype).to_string()
        if ti.cfg.arch == ti.cc:
            self.dtype_str = 'Ti_' + dtype_str
        else:
            self.dtype_str = {
                'i32': 'int',
                'i64': 'int64_t',
                'f32': 'float',
                'f64': 'double',
            }[dtype_str]
        self._define()

    @ti.func
    def _define(self):
        ti.asm(f'{self.dtype_str} {self.name}[{self.size}]')

    @ti.func
    def subscript(self, idx):
        ret = ti.cast(0, self.dtype)
        ti.asm(f'$0 = {self.name}[%0]', inputs=[idx], outputs=[ret])
        self._override_assign(ret, idx)
        return ret

    def _override_assign(self, var, idx):
        def assign(val):
            ti.asm(f'{self.name}[%0] = %1', inputs=[idx, val])

        var.assign = assign
        return var

    def variable(self):
        return self


if __name__ == '__main__':
    ti.init(ti.cc, log_level=ti.DEBUG)

    @ti.kernel
    def func():
        for _ in range(1):
            a = LocalArray(int, 3)
            for i in range(3):
                a[i] = i
            for i in range(3):
                print(a[i])

    func()
