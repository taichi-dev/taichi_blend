import numblend as nb
import taichi as ti
import numpy as np
import bpy

nb.init()
ti.init(arch=ti.cpu)


N = 16

pos = ti.Vector.field(3, float, N)


@ti.kernel
def init():
    for i in pos:
        pos[i] = ti.Vector([i - N / 2, 0, 0])


@ti.kernel
def update(t: float):
    for i in pos:
        pos[i].z = ti.sin(pos[i].x * 0.5 - t)



objects = []
for i in range(N):
    nb.delete_object(f'cube_{i}')
    bpy.ops.mesh.primitive_cube_add(size=1)
    bpy.context.object.name = f'cube_{i}'
    objects.append(bpy.context.object)


@nb.add_animation
def main():
    init()
    for frame in range(250):
        update(frame * 0.03)
        yield nb.objects_update(objects, location=pos.to_numpy())
