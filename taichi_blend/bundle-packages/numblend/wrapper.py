'''Blender API wrappers'''

from .common import np_array
from .numio import from_numpy, to_numpy
import bpy


# Stop-motion-OBJ
def object_frames(obj):
    if isinstance(obj, str):
        obj = bpy.data.objects[obj]
    return (bpy.data.meshes[x.key] for x in obj.mesh_sequence_settings.meshNameArray)


# Stop-motion-OBJ
def set_object_frame(obj, i, mesh):
    if isinstance(obj, str):
        obj = bpy.data.objects[obj]
    obj.mesh_sequence_settings.meshNameArray[i].key = mesh.name


def new_mesh(name, pos=[], edges=[], faces=[], uv=None):
    pos = np_array(pos)
    edges = np_array(edges)
    faces = np_array(faces)
    uv = np_array(uv)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(pos.tolist(), edges.tolist(), faces.tolist())
    if uv is not None:
        mesh.uv_layers.new()
        from_numpy(mesh.uv_layers.active.data, 'uv', uv)
    return mesh


def new_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    col = bpy.context.collection
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


def get_object(name):
    return bpy.data.objects[name]


def get_mesh(name):
    return bpy.data.meshes[name]


def delete_mesh(name):
    try:
        obj = bpy.data.meshes[name]
    except KeyError:
        return False
    bpy.data.meshes.remove(obj)
    return True


def delete_object(name):
    try:
        obj = bpy.data.objects[name]
    except KeyError:
        return False
    bpy.data.objects.remove(obj)
    return True
