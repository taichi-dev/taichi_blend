from common import *


@ti.test(ti.cpu)
def test_copy():
    ret = ti.Vector.field(3, int, [])

    @ti.kernel
    def main():
        x = namespace()
        x.a = 1
        y = x.copy()
        z = x.copy()
        x.a = 3
        z.a = 2
        ret[None] = x.a, y.a, z.a

    main()
    assert np.all(ret.to_numpy() == [3, 1, 2])


@ti.test(ti.cpu)
def test_funcarg():
    ret = ti.Vector.field(3, int, [])

    @ti.func
    def calc(x):
        y = namespace()
        y.w = x.a + x.b
        y.u = x.b
        y.u -= 2
        y.z = 4
        return y

    @ti.kernel
    def main():
        x = namespace()
        x.a = 3
        x.b = 4
        y = calc(x)
        ret[None] = y.w, y.u, y.z

    main()
    assert np.all(ret.to_numpy() == [7, 2, 4])


@ti.test(ti.cpu)
def test_class():
    ret = ti.Vector.field(4, int, [])

    @ti.data_oriented
    class MyData(namespace):
        @ti.func
        def __init__(self, z):
            self.x = 1
            self.y = 2
            self.z = z - 1

        @ti.func
        def calc_w(self):
            return self.x + self.y + self.z

    @ti.kernel
    def main():
        a = MyData(4)
        w = a.calc_w()
        ret[None] = a.x, a.y, a.z, w

    main()
    assert np.all(ret.to_numpy() == [1, 2, 3, 6])


@ti.test(ti.cpu)
def test_assign():
    r = ti.field(int, [])
    s = ti.field(float, [])

    @ti.kernel
    def main():
        x = namespace(a=1, b=3.1)
        x = namespace(a=3, b=4)
        r[None], s[None] = x.a, x.b

    main()
    assert r[None] == 3
    assert s[None] == 4.0
