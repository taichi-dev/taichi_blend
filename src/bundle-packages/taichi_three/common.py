import taichi as ti
import numpy as np

from .hacker import *


def V(*xs):
    return ti.Vector(xs)


def V23(xy, z):
    return V(xy.x, xy.y, z)


def V34(xyz, w):
    return V(xyz.x, xyz.y, xyz.z, w)


ti.Matrix.xy = property(lambda v: V(v.x, v.y))
ti.Matrix.xyz = property(lambda v: V(v.x, v.y, v.z))


def totuple(x):
    if x is None:
        x = []
    if isinstance(x, ti.Matrix):
        x = x.entries
    if isinstance(x, list):
        x = tuple(x)
    if not isinstance(x, tuple):
        x = x,
    if isinstance(x, tuple) and len(x) and x[0] is None:
        x = []
    return x


def tovector(x):
    return ti.Vector(totuple(x))


def vconcat(*xs):
    res = []
    for x in xs:
        if isinstance(x, ti.Matrix):
            res.extend(x.entries)
        else:
            res.append(x)
    return ti.Vector(res)


@ti.func
def clamp(x, xmin, xmax):
    return min(xmax, max(xmin, x))


@ti.func
def ifloor(x):
    return int(ti.floor(x))


@ti.func
def iceil(x):
    return int(ti.ceil(x))


@ti.func
def bilerp(f: ti.template(), pos):
    p = float(pos)
    I = int(ti.floor(p))
    x = p - I
    y = 1 - x
    return (f[I + V(1, 1)] * x[0] * x[1] +
            f[I + V(1, 0)] * x[0] * y[1] +
            f[I + V(0, 0)] * y[0] * y[1] +
            f[I + V(0, 1)] * y[0] * x[1])


@ti.func
def mapply(mat, pos, wei):
    res = ti.Vector([mat[i, 3] for i in range(3)]) * wei
    for i, j in ti.static(ti.ndrange(3, 3)):
        res[i] += mat[i, j] * pos[j]
    rew = mat[3, 3] * wei
    for i in ti.static(range(3)):
        rew += mat[3, i] * pos[i]
    return res, rew


@ti.func
def mapply_pos(mat, pos):
    res, rew = mapply(mat, pos, 1)
    return res / rew

@ti.func
def mapply_dir(mat, pos):
    res, rew = mapply(mat, pos, 0)
    return res


@ti.pyfunc
def reflect(I, N):
    return I - 2 * N.dot(I) * N


@ti.pyfunc
def lerp(fac, src, dst):
    return src * (1 - fac) + dst * fac


import taichi_three as tina
