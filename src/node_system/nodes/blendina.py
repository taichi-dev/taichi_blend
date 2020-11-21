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
    Inputs: target:so override:b
    Output: create:t object:a
    '''
    def __init__(self, name, override=False):
        self.name = name
        self.override = override

    def run(self):
        if self.override:
            mesh = new_mesh(self.name)
            new_object(self.name, mesh)


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

        # Make the stupid `StructRNA` happy:
        old_name = self.object.name
        object = bpy.data.objects[old_name]
        old_mesh = object.data.name
        new_mesh = None

        @bpy.app.handlers.persistent
        def save_pre(self):
            try:
                nonlocal new_mesh
                object = bpy.data.objects[old_name]
                new_mesh = object.data.name
                object.data = bpy.data.meshes[old_mesh]
            except Exception as e:
                print('save_pre', repr(e))

        @bpy.app.handlers.persistent
        def save_post(self):
            try:
                object = bpy.data.objects[old_name]
                object.data = bpy.data.meshes[new_mesh]
            except Exception as e:
                print('save_post', repr(e))

        bpy.app.handlers.save_pre.append(save_pre)
        bpy.app.handlers.save_post.append(save_post)

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
        object = bpy.data.objects[self.object.name]
        object.data = bpy.data.meshes[mesh_name]


@A.register
class RenderOutput(INode):
    '''
    Name: render_output
    Category: output
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
def OutputMeshAnimation(target, override, verts, start, update):
    '''
    Name: output_mesh_animation
    Category: output
    Inputs: target:so override:b verts:vf start:t update:t
    Output:
    '''

    object = NewMeshObject(target, override)
    start = A.merge_tasks(object, start)
    update = MeshSequence(object, verts, update)
    return OutputTasks(start, update)


@A.register
class OutputTasks(INode):
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


@A.register
def Router(a):
    '''
    Name: socket_router
    Category: misc
    Inputs: a:a
    Output: a:a
    '''

    return a


@A.register
class DebugInfo:
    '''
    Name: debug_info
    Category: misc
    Inputs: data:a
    Output:
    '''

    def __init__(self, data):
        self.data = data


def register():
    pass


def unregister():
    pass
