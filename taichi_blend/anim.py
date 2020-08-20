'''Blender real-time animation'''

import bpy
import copy
from .numio import from_numpy, to_numpy


anim_hooks = []


def anim_update_frame(scene, *args):
    global anim_hooks
    assert scene == bpy.context.scene
    frame = scene.frame_current
    for cb in anim_hooks:
        cb(frame)


def anim_iter_hook(mesh):
    import copy

    def decorator(iterator):
        iterator = iterator()
        cache = []

        def on_anim(frame):
            while len(cache) <= frame:
                data = next(iterator)
                #data = copy.deepcopy(data)
                cache.append(data)
            data = cache[frame]

            if not isinstance(data, tuple):
                data = (data,)

            if len(data) > 0:
                from_numpy(mesh.vertices, 'co', data[0])

            if len(data) > 1:
                from_numpy(mesh.edges, 'vertices', data[1])

            if len(data) > 2:
                from_numpy(mesh.polygons, 'vertices', data[2])

            mesh.update()

        return on_anim

    return decorator
