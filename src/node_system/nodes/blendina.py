import numpy as np
from tina import *
import bpy


def to_numpy(b, key):
    dim = len(getattr(b[0], key))
    seq = [0] * (len(b) * dim)
    b.foreach_get(key, seq)
    return np.array(seq).reshape(len(b), dim)


def from_numpy(b, key, a):
    dim = len(getattr(b[0], key)) if len(b) else a.shape[1]
    assert len(a.shape) == 2
    assert a.shape[1] == dim, dim
    if len(b) < a.shape[0]:
        b.add(a.shape[0] - len(b))
    seq = a.reshape(a.shape[0] * dim).tolist()
    seq = seq + [0] * (len(b) * dim - len(seq))
    b.foreach_set(key, seq)


def mesh_update(mesh, verts=None, edges=None, faces=None):
    if verts is not None:
        from_numpy(mesh.vertices, 'co', verts)
    if edges is not None:
        from_numpy(mesh.edges, 'vertices', edges)
    if faces is not None:
        from_numpy(mesh.polygons, 'vertices', faces)
    mesh.update()


def delete(array, name):
    if name in array:
        array.remove(array[name])


def new_mesh(name, verts=None, edges=None, faces=None):
    delete(bpy.data.meshes, name)
    mesh = bpy.data.meshes.new(name)
    verts = verts.tolist() if verts is not None else []
    edges = edges.tolist() if edges is not None else []
    faces = faces.tolist() if faces is not None else []
    mesh.from_pydata(verts, edges, faces)
    return mesh


def new_object(name, mesh):
    delete(bpy.data.objects, name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


@A.register
class NewMeshObject(IRun):
    '''
    Name: new_mesh_object
    Category: blender
    Inputs: target:so
    Output: create:t object:a
    '''
    def __init__(self, name):
        self.name = name
        self.object = None

    def run(self):
        self.mesh = new_mesh(self.name)
        self.object = new_object(self.name, self.mesh)

    def __del__(self):
        delete(bpy.data.meshes, self.name)
        delete(bpy.data.objects, self.name)


@A.register
class MeshSequence(IRun):
    '''
    Name: mesh_sequence
    Category: blender
    Inputs: object:a verts:vf update:t
    Output: update:t
    '''
    def __init__(self, object, verts, update):
        assert isinstance(verts, IField)
        assert isinstance(object, NewMeshObject)
        assert isinstance(update, IRun)

        self.verts = verts
        self.object = object
        self.update = update

        self.cache = []

    @ti.kernel
    def _export(self, f: ti.template(), out: ti.ext_arr(), dim: ti.template()):
        for I in ti.static(f):
            for j in ti.static(range(dim)):
                out[I, j] = f[I][j]

    def mesh_update(self, mesh):
        self.update.run()
        verts = np.empty((*self.verts.meta.shape, 3))
        self._export(self.verts, verts, 3)
        mesh_update(mesh, verts)

    def run(self):
        frame = bpy.context.scene.frame_current
        frame = max(frame, bpy.context.scene.frame_start)
        frame = min(frame, bpy.context.scene.frame_end)
        frameid = frame - bpy.context.scene.frame_start

        while len(self.cache) <= frameid:
            frame = len(self.cache) + bpy.context.scene.frame_start
            mesh_name = f'{self.object.name}_{frame:03d}'
            mesh = new_mesh(mesh_name)

            self.mesh_update(mesh)
            self.cache.append(mesh_name)

        mesh_name = self.cache[frameid]
        self.object.object.data = bpy.data.meshes[mesh_name]

    def __del__(self):
        for mesh_name in self.cache:
            delete(bpy.data.meshes, mesh_name)


@A.register
@ti.data_oriented
class RenderOutput:
    '''
    Name: render_output
    Category: blender
    Inputs: image:vf
    Output:
    '''
    def __init__(self, img):
        assert isinstance(img, IField)

        self.img = img

    def _cook(self, color):
        if isinstance(color, ti.Expr):
            color = ti.Vector([color, color, color])
        elif isinstance(color, ti.Matrix):
            assert color.m == 1, color.m
            if color.n == 1:
                color = ti.Vector([color(0), color(0), color(0)])
            elif color.n == 2:
                color = ti.Vector([color(0), color(1), 0])
            elif color.n in [3, 4]:
                color = ti.Vector([color(0), color(1), color(2)])
            else:
                assert False, color.n
        return color

    @ti.func
    def image_at(self, i, j, width, height):
        ti.static_assert(len(self.img.meta.shape) == 2)
        scale = ti.Vector(self.img.meta.shape) / ti.Vector([width, height])
        pos = ti.Vector([i, j]) * scale
        color = bilerp(self.img, pos)
        return self._cook(color)

    @ti.kernel
    def render(self, out: ti.ext_arr(), width: int, height: int):
        for i, j in ti.ndrange(width, height):
            r, g, b = self.image_at(i, j, width, height)
            base = (j * width + i) * 4
            out[base + 0] = r
            out[base + 1] = g
            out[base + 2] = b
            out[base + 3] = 1


@A.register
class CurrentFrame(A.uniform_field, IRun):
    '''
    Name: current_frame
    Category: parameter
    Inputs:
    Output: frame:f update:t
    '''

    def __init__(self):
        super().__init__(Field(Meta([], int, [])))

    def run(self):
        self.value[None] = bpy.context.scene.frame_current


@A.register
class OutputTasks(IRun):
    '''
    Name: output_tasks
    Category: output
    Inputs: start:t update:t
    Output:
    '''
    def __init__(self, start, update):
        assert isinstance(start, IRun)
        assert isinstance(update, IRun)
        self.start = start
        self.update = update


@A.register
def FVPack3(x, y, z):
    '''
    Name: pack_3d_vector
    Category: converter
    Inputs: x:f y:f z:f
    Output: vector:vf
    '''

    return A.pack_vector(x, y, z)


def register():
    pass


def unregister():
    pass
