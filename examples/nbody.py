import taichi_blend as tb
import taichi_glsl as tl
import taichi as ti
import numpy as np
import bpy

tb.register()
ti.init(arch=ti.cuda)


# physics settings
N = 2048
dt = 1e-2
gravity = 0.055


# delete old mesh & object (if any)
tb.delete_mesh('point_cloud')
tb.delete_object('point_cloud')

# create a new point cloud
mesh = tb.new_mesh('point_cloud', np.zeros((N, 3)))
object = tb.new_object('point_cloud', mesh)


# declare Taichi fields
x = ti.Vector.field(3, float, N)
v = ti.Vector.field(3, float, N)


# define Taichi kernels
@ti.kernel
def init():
    for i in x:
        r = tl.randInt(0, 2) * 2 - 1
        x[i] = tl.randUnit3D() + r * 7
        v[i].x = 0.1 * r


@ti.kernel
def substep():
    for i in x:
        acc = ti.Vector.zero(float, 3)
        for j in range(N):
            r = x[i] - x[j]
            acc -= r / r.norm(1e-2)**3
        v[i] += gravity * acc * dt
    for i in x:
        x[i] += v[i] * dt


# define animation iterator body
@tb.anim_iter_hook(mesh)
def main():
    init()
    yield x.to_numpy()
    while True:
        for s in range(6):
            substep()
        yield x.to_numpy()

# hook animation iterator
tb.anim_hooks.clear()
tb.anim_hooks.append(main)
