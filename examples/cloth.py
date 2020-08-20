import taichi as ti
import taichi_glsl as tl
import taichi_three as t3
import taichi_blend as tb
import numpy as np
import bpy

ti.init(arch=ti.cuda)

### Parameters

N = 128
NN = N, N
W = 1
L = W / N
gravity = 0.5
stiffness = 1600
damping = 2
steps = 30
dt = 5e-4

### Physics

x = ti.Vector.field(3, float, NN)
v = ti.Vector.field(3, float, NN)


@ti.kernel
def init():
    for i in ti.grouped(x):
        x[i] = tl.vec((i + 0.5) * L - 0.5, 0.8).xzy


links = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
links = [tl.vec(*_) for _ in links]


@ti.kernel
def substep():
    for i in ti.grouped(x):
        acc = x[i] * 0
        for d in ti.static(links):
            disp = x[tl.clamp(i + d, 0, tl.vec(*NN) - 1)] - x[i]
            length = L * float(d).norm()
            acc += disp * (disp.norm() - length) / length**2
        v[i] += stiffness * acc * dt
    for i in ti.grouped(x):
        v[i].y -= gravity * dt
        v[i] = tl.ballBoundReflect(x[i], v[i], tl.vec(+0.0, +0.2, -0.0), 0.4, 6)
    for i in ti.grouped(x):
        v[i] *= ti.exp(-damping * dt)
        x[i] += dt * v[i]


### Blender

_, edges, faces, uv = tb.meshgrid(N)

tb.delete_mesh('point_cloud')
tb.delete_object('point_cloud')

mesh = tb.new_mesh('point_cloud', np.zeros((N**2, 3)), edges, faces)
object = tb.new_object('point_cloud', mesh)

@tb.anim_iter_hook(mesh)
def main():
    def T(x):
        return np.array([x[:, 0], x[:, 2], x[:, 1]]).swapaxes(0, 1)

    init()
    yield T(x.to_numpy().reshape(N**2, 3))
    while True:
        for s in range(steps):
            substep()
        yield T(x.to_numpy().reshape(N**2, 3))

tb.anim_hooks.clear()
tb.anim_hooks.append(main)
