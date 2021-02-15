from common import *


@ti.test(ti.cpu)
def test_scalar():
    @multireturn
    @ti.func
    def func(x):
        yield 0.0

        if x < 0:
            yield -1.0

        yield ti.sqrt(x)

    r = ti.field(float, 2)

    @ti.kernel
    def main():
        r[0] = func(-4)
        r[1] = func(4)

    main()

    assert np.allclose(r.to_numpy(), [-1, 2])


@ti.test(ti.cpu)
def test_listspace():
    @multireturn
    @ti.func
    def func(x):
        yield listspace(0.0, 1)

        if x < 0:
            yield -1.0, 0

        yield ti.sqrt(x), 1

    r = ti.field(float, 2)
    s = ti.field(int, 2)

    @ti.kernel
    def main():
        r[0], s[0] = func(-4)
        r[1], s[1] = func(4)


    main()

    assert np.allclose(r.to_numpy(), [-1, 2])
    assert np.all(s.to_numpy() == [0, 1])


@ti.test(ti.cpu)
def test_namespace():
    @multireturn
    @ti.func
    def func(x):
        yield namespace(x=0.0, y=1)

        if x < 0:
            yield namespace(x=-1.0, y=0)

        yield namespace(x=ti.sqrt(x), y=1)

    r = ti.field(float, 2)
    s = ti.field(int, 2)

    @ti.kernel
    def main():
        a = func(-4)
        b = func(4)
        print(a.x, a.y)
        print(b.x, b.y)
        r[0], s[0] = a.x, a.y
        r[1], s[1] = b.x, b.y


    main()
    exit()

    assert np.allclose(r.to_numpy(), [-1, 2])
    assert np.all(s.to_numpy() == [0, 1])
