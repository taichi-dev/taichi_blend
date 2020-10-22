import numblend as nb
import taichi_glsl as tl
import taichi as ti
import numpy as np
import bpy

nb.init()
ti.init(arch=ti.cuda)


dt = 6e-3
steps = 5
gravity = 9.8
bound = 3
radius = 0.5
N = 64

x = ti.Vector.field(3, float, N)
v = ti.Vector.field(3, float, N)
u = ti.Vector.field(3, float, N)


@ti.kernel
def init():
    for i in x:
        x[i] = (tl.randND(3) * 2 - 1) * (bound - radius)
        v[i] = tl.randUnit3D() * 4


@ti.kernel
def substep():
    for i in x:
        x[i] += v[i] * dt
        u[i] = v[i]
        for j in range(N):
            if i == j: continue
            r = x[i] - x[j]
            if r.norm_sqr() <= (radius * 2)**2 and r.dot(v[i] - v[j]) < 0:
                    u[i], _ = tl.momentumExchange(u[i], v[j], r.normalized(), 1.0, 1.0, 0.9)
    for i in x:
        v[i] = u[i]
        v[i].z -= gravity * dt
        v[i] = tl.boundReflect(x[i], v[i], radius - bound, bound - radius, 0.87, 0.92)


objects = []

for i in range(N):
    nb.delete_object(f'ball_{i}')
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5)
    bpy.ops.object.shade_smooth()
    bpy.context.object.name = f'ball_{i}'
    objects.append(bpy.context.object)

@nb.add_animation
def main():
    init()
    while True:
        for s in range(steps):
            substep()
        pos = x.to_numpy()
        ret = nb.AnimUpdate()
        for i in range(N):
            ret += nb.object_update(objects[i], location=pos[i])
        yield ret
