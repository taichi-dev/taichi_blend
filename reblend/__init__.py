import bpy
import numpy as np


def blender_to_numpy(b):
    ret = []
    for i in range(len(b)):
        ret.append([_ for _ in b[i].co])
    return np.array(ret)

def blender_from_numpy(b, a):
    for i in range(min(a.shape[0], len(b))):
        for j in range(len(b[i].co)):
            b[i].co[j] = a[i, j]


def iter_object_frames(object):
    if isinstance(object, str):
        object = bpy.data.objects[object]
    return (bpy.data.meshes[x.key] for x in object.mesh_sequence_settings.meshNameArray)


__all__ = '''
np
bpy
iter_object_frames
blender_from_numpy
blender_to_numpy
'''.strip().splitlines()
