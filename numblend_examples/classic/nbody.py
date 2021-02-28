import numblend as nb
import taichi_glsl as tl
import taichi as ti
import numpy as np
import bpy

nb.init()
ti.init(arch=ti.cuda)


# physics settings
N = 2048
dt = 1e-2
gravity = 0.055


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


# delete old mesh & object (if any)
nb.delete_mesh('point_cloud')
nb.delete_object('point_cloud')

# create a new point cloud
mesh = nb.new_mesh('point_cloud', np.zeros((N, 3)))
object = nb.new_object('point_cloud', mesh)


# define animation iterator body
@nb.add_animation
def main():
    init()
    while True:
        for s in range(6):
            substep()
        yield nb.mesh_update(mesh, x.to_numpy())
