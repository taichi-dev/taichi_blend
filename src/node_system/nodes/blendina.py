import numpy as np
from tina import *
import bpy


def to_numpy(b, key, dim=None):
    if dim is None:
        dim = len(getattr(b[0], key))
    seq = [0] * (len(b) * dim)
    b.foreach_get(key, seq)
    return np.array(seq)


def from_numpy(b, key, a, dim=None):
    if dim is None:
        dim = len(getattr(b[0], key))
    assert len(a.shape) == 1
    if len(b) < a.shape[0]:
        b.add(a.shape[0] - len(b))
    seq = a.tolist()  # bottleneck
    if len(seq) < len(b) * dim:
        seq = seq + [0] * (len(b) * dim - len(seq))
    b.foreach_set(key, seq)


def mesh_update(mesh, verts=None, edges=None, faces=None, npoly=None):
    if verts is not None:
        from_numpy(mesh.vertices, 'co', verts, 3)
    if edges is not None:
        from_numpy(mesh.edges, 'vertices', edges, 2)
    if faces is not None:
        from_numpy(mesh.polygons, 'vertices', faces, npoly)
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


@ti.kernel
def export_vfield(f: ti.template(), out: ti.ext_arr(), dim: ti.template()):
    for I in ti.static(f):
        vec = f[I]
        for j in ti.static(range(dim)):
            out[I[0] * dim + j] = vec[j]


@A.register
class NewMeshObject(IRun):
    '''
    Name: new_mesh_object
    Category: blender
    Inputs: target:so preserve:b
    Output: create:t object:a
    '''
    def __init__(self, name, preserve=False):
        self.name = name
        self.preserve = preserve

    def run(self):
        if not self.preserve:
            mesh = new_mesh(self.name)
            new_object(self.name, mesh)


@A.register
class MeshSequence(IRun):
    '''
    Name: mesh_sequence
    Category: blender
    Inputs: object:a update:t verts:vf
    Output: update:t
    '''
    def __init__(self, object, update, verts):
        assert isinstance(object, NewMeshObject)
        assert isinstance(update, IRun)
        assert isinstance(verts, IField)

        self.verts = verts
        self.object = object
        self.update = update

        self.cache = []

        if self.object.preserve:
            # Make the stupid `StructRNA` happy:
            old_name = self.object.name

            @bpy.app.handlers.persistent
            def save_pre(self):
                try:
                    print('save_pre', old_name)
                    object = bpy.data.objects[old_name]
                    object.data = bpy.data.meshes[old_name]
                except Exception as e:
                    print('save_pre', repr(e))

            bpy.app.handlers.save_pre.append(save_pre)

    def update_data(self):
        self.update.run()
        assert len(self.verts.meta.shape) == 1, 'please use A.flatten_field'
        verts = np.empty(self.verts.meta.shape[0] * 3)
        export_vfield(self.verts, verts, 3)
        return verts,

    def run(self):
        frame = bpy.context.scene.frame_current
        frame = max(frame, bpy.context.scene.frame_start)
        frame = min(frame, bpy.context.scene.frame_end)
        frameid = frame - bpy.context.scene.frame_start

        while len(self.cache) <= frameid:
            frame = len(self.cache) + bpy.context.scene.frame_start
            mesh_name = f'{self.object.name}_{frame:03d}'
            data = self.update_data()
            mesh = new_mesh(mesh_name)#, *data)
            mesh_update(mesh, *data)
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
def OutputMeshAnimation(target, preserve, verts, start, update):
    '''
    Name: output_mesh_animation
    Category: output
    Inputs: target:so preserve:b verts:vf start:t update:t
    Output:
    '''

    object = NewMeshObject(target, preserve)
    start = A.merge_tasks(object, start)
    update = MeshSequence(object, update, verts)
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
