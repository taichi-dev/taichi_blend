import numblend as nb
import taichi_glsl as tl
import taichi as ti
import numpy as np
import bpy

nb.init()
ti.init(arch=ti.cpu)


N = 128
dt = 0.1

pos = ti.Vector.field(3, float, (N, N))
vel = ti.Vector.field(3, float, (N, N))


@ti.kernel
def init():
    for i, j in pos:
        pos[i, j] = ti.Vector([i - N / 2, j - N / 2, 0])
        vel[i, j] = ti.Vector([0, 0, 0])


@ti.kernel
def update():
    for i, j in ti.ndrange((1, N - 1), (1, N - 1)):
        pos[i, j].z += vel[i, j].z * dt
        laplace_z = pos[i - 1, j].z + pos[i + 1, j].z + pos[i, j - 1].z + pos[i, j + 1].z - pos[i, j].z * 4
        vel[i, j].z += 0.1 * laplace_z * dt


@ti.kernel
def random_touch():
    x = int(ti.random() * N)
    y = int(ti.random() * N)
    for i, j in ti.ndrange((1, N - 1), (1, N - 1)):
        pos[i, j].z += 8 * ti.exp(-0.06 * ti.Vector([x - i, y - j]).norm_sqr())


verts, edges, faces, uv = nb.meshgrid(N)
nb.delete_object('point_cloud')
nb.delete_mesh('point_cloud')
mesh = nb.new_mesh('point_cloud', verts, edges, faces, uv)
nb.new_object('point_cloud', mesh)


@nb.add_animation
def main():
    init()
    for frame in range(250):
        if frame % 40 == 0:
            random_touch()
        for step in range(10):
            update()
        yield nb.mesh_update(mesh, pos=pos.to_numpy().reshape(N**2, 3))
