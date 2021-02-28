import numblend as nb
import taichi_glsl as tl
import taichi as ti
import numpy as np
import bpy

nb.init()
ti.init(arch=ti.cpu)


N = 16

pos = ti.Vector.field(3, float, (N, N))


@ti.kernel
def init():
    for i, j in pos:
        pos[i, j] = ti.Vector([i - N / 2, j - N / 2, 0])


@ti.kernel
def update(t: float):
    for i, j in pos:
        pos[i, j].z = ti.sin(pos[i, j].xy.norm() * 0.5 - t * 2)



nb.delete_mesh('point_cloud')
nb.delete_object('point_cloud')
mesh = nb.new_mesh('point_cloud')
nb.new_object('point_cloud', mesh)


@nb.add_animation
def main():
    init()
    for frame in range(250):
        update(frame * 0.03)
        yield nb.mesh_update(mesh, pos=pos.to_numpy().reshape(N**2, 3))
