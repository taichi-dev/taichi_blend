from tina.common import *


@ti.func
def schlickFresnel(cost):
    return clamp(1 - cost, 0, 1)**5


@ti.func
def dielectricFresnel(etai, etao, cosi):
    sini = ti.sqrt(max(0, 1 - cosi**2))
    sint = etao / etai * sini

    ret = 1.0
    if sint < 1:
        cost = ti.sqrt(max(0, 1 - sint**2))
        a1, a2 = etai * cosi, etao * cost
        b1, b2 = etao * cosi, etai * cost
        para = (a1 - a2) / (a1 + a2)
        perp = (b1 - b2) / (b1 + b2)
        ret = 0.5 * (para**2 + perp**2)

    return ret


@ti.func
def GTR1(cosh, alpha):
    alpha2 = alpha**2
    t = 1 + (alpha2 - 1) * cosh**2
    return (alpha2 - 1) / (ti.pi * ti.log(alpha2) * t)


@ti.func
def GTR2(cosh, alpha):
    alpha2 = alpha**2
    t = 1 + (alpha2 - 1) * cosh**2
    return alpha2 / (ti.pi * t**2)


@ti.func
def smithGGX(cosi, alpha):
    a = alpha**2
    b = cosi**2
    return 1 / (cosi + ti.sqrt(a + b - a * b))


@ti.func
def smithGTR2(cosi, alpha):
    tani2 = (1 - cosi**2) / cosi**2
    return 2 / (1 + ti.sqrt(1 + alpha**2 * tani2))


@ti.func
def sample_GTR1(u, v, alpha):
    u = ti.sqrt(alpha**(2 - 2 * u) - 1) / (alpha**2 - 1)
    return spherical(u, v)


@ti.func
def sample_GTR2(u, v, alpha):
    u = ti.sqrt((1 - u) / (1 - u * (1 - alpha**2)))
    return spherical(u, v)


# https://github.com/AirGuanZ/Atrc/blob/6a6c84c265261be0ac62ad8783a62cd9257549c1/src/tracer/src/core/material/utility/microfacet.cpp#L104
@ti.func
def sample_GTR2_vnor(ve, u, v, alpha):
    vh = V23(alpha * ve.xy, ve.z).normalized()
    lensq = vh.xy.norm_sqr()
    t1 = V(1.0, 0.0, 0.0)
    if lensq > eps:
        t1 = V(-vh.y, vh.x, 0.0) / ti.sqrt(lensq)
    t2 = vh.cross(t1)

    r = ti.sqrt(u)
    phi = ti.tau * v
    t_1 = r * ti.cos(phi)
    _t_2 = r * ti.sin(phi)
    s = 0.5 * (1 + vh.z)
    t_2 = (1 - s) * ti.sqrt(1 - t_1**2) + s * _t_2

    nh = t_1 * t1 + t_2 * t2 + ti.sqrt(max(0, 1 - t_1**2 - t_2**2)) * vh
    ne = V23(alpha * nh, max(0, nh.z)).normalized()

    return ne
