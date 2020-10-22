import taichi as ti
import taichi_glsl as tl
import numblend as nb
import numpy as np
import bpy

nb.init()
ti.init(ti.cuda)

N = 64
shortening = 1
stiffness = 2000
damping = 1.6
dt = 5e-4
steps = 144
gravity = 9.8
wind = 0.1
ball_radius = 0.4

pos_, edges_, faces_, uv_ = nb.meshgrid(N, eight=True)
pos_[:, :2] = pos_[:, :2] * 2 - 1
pos_ = pos_[:, (2, 1, 0)]

rest_ = np.sqrt(np.sum((pos_[edges_[:, 0]] - pos_[edges_[:, 1]])**2, axis=1))

nb.delete_mesh('cloth')
nb.delete_object('cloth')
nb.delete_object('ball')
cloth_mesh = nb.new_mesh('cloth', pos_, nb.meshgrid(N)[1], faces_, uv_)
cloth_object = nb.new_object('cloth', cloth_mesh)

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=ball_radius)
ball_object = bpy.context.object
ball_object.name = 'ball'

pos = ti.Vector.field(3, float, pos_.shape[0])
vel = ti.Vector.field(3, float, pos_.shape[0])
edges = ti.Vector.field(2, int, edges_.shape[0])
rest = ti.field(float, rest_.shape[0])
pos.from_numpy(pos_)
edges.from_numpy(edges_)
rest.from_numpy(rest_)

@ti.kernel
def substep(bx: float, bz: float):
    for e in edges:
        i, j = edges[e]
        if i == j: continue
        r = pos[i] - pos[j]
        l = rest[e] * shortening
        acc = stiffness * dt * r * (r.norm() - l) / l**2
        vel[i] -= acc
        vel[j] += acc
    for i in pos:
        if pos[i].z == 1 and abs(pos[i].y) == 1:
            continue
        vel[i].z -= gravity * dt
        vel[i].x -= wind * dt
        vel[i] = tl.ballBoundReflect(pos[i], vel[i], tl.vec(bx, 0.0, bz), ball_radius + 0.03, 6)
        vel[i] *= ti.exp(-dt * damping)
        pos[i] += vel[i] * dt


@nb.add_animation
def main():
    for i in range(500):
        print('rendering frame', i)
        for s in range(steps):
            t = (i + s / steps) * 0.03
            bx, bz = ti.cos(t) * 0.7, -ti.sin(t) * 0.7
            substep(bx, bz)
        yield nb.mesh_update(cloth_mesh, pos.to_numpy()) \
            + nb.object_update(ball_object, location=[bx, 0, bz])
