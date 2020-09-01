'''Blender real-time animation'''

import bpy
import copy
from .numio import from_numpy, to_numpy


anim_hooks = []


def clear_animations():
    anim_hooks.clear()


def update_frame_callback(scene, *args):
    assert scene == bpy.context.scene
    frame = scene.frame_current
    for cb in anim_hooks:
        cb(frame)


def animation(iterator):
    import copy

    iterator = iterator()
    cache = []

    def wrapped(frame):
        while len(cache) <= frame:
            func = next(iterator)
            cache.append(func)

        func = cache[frame]
        func()

    anim_hooks.append(wrapped)
    return wrapped


class AnimUpdate:
    def __init__(self, callback):
        self.callback = callback

    def __add__(self, other):
        def callback(*args, **kwargs):
            self.callback(*args, **kwargs)
            other.callback(*args, **kwargs)
        AnimUpdate(callback)

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)


def mesh_update(mesh, pos=None, edges=None, faces=None):
    def callback():
        if pos is not None:
            from_numpy(mesh.vertices, 'co', pos)
        if edges is not None:
            from_numpy(mesh.edges, 'vertices', edges)
        if faces is not None:
            from_numpy(mesh.polygons, 'vertices', faces)
        mesh.update()
    return AnimUpdate(callback)
