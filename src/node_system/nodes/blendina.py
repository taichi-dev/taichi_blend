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


def new_mesh(name, verts=None, edges=None, faces=None):
    if name in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[name])
    mesh = bpy.data.meshes.new(name)
    verts = verts.tolist() if verts is not None else []
    edges = edges.tolist() if edges is not None else []
    faces = faces.tolist() if faces is not None else []
    mesh.from_pydata(verts, edges, faces)
    return mesh


def new_object(name, mesh):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj


@A.register
class NewEmptyMesh(IRun):
    '''
    Name: new_empty_mesh
    Category: output
    Inputs: target:so
    Output: task:t mesh:a
    '''
    def __init__(self, name):
        self.name = name
        self.object = None

    def run(self):
        self.mesh = new_mesh(self.name)
        self.object = new_object(self.name, self.mesh)


@A.register
class MeshUpdate(IRun):
    '''
    Name: mesh_update
    Category: output
    Inputs: mesh:a verts:vf
    Output: task:t
    '''
    def __init__(self, mesh, verts):
        assert isinstance(verts, IField)
        assert isinstance(mesh, NewEmptyMesh)

        self.verts = verts
        self.mesh = mesh

    @ti.kernel
    def _export(self, f: ti.template(), out: ti.ext_arr(), dim: ti.template()):
        for I in ti.static(f):
            for j in ti.static(range(dim)):
                out[I, j] = f[I][j]

    def run(self):
        mesh = self.mesh.mesh

        verts = np.empty((*self.verts.meta.shape, 3))
        self._export(self.verts, verts, 3)

        mesh_update(mesh, verts)


@A.register
class CurrentFrameId(A.uniform_field, IRun):
    '''
    Name: current_frame_id
    Category: parameter
    Inputs:
    Output: frame:f update:t
    '''

    def __init__(self):
        super().__init__(Field(Meta([], int, [])))

    def run(self):
        self.value[None] = bpy.context.scene.frame_current


@A.register
@ti.data_oriented
class RenderOutput:
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
class OnStart(IRun):
    '''
    Name: on_start
    Category: output
    Inputs: task:t
    Output:
    '''
    def __init__(self, task):
        assert isinstance(task, IRun)
        self.task = task

    def run(self):
        self.task.run()


@A.register
class OnUpdate(IRun):
    '''
    Name: on_update
    Category: output
    Inputs: task:t
    Output:
    '''
    def __init__(self, task):
        assert isinstance(task, IRun)
        self.task = task

    def run(self):
        self.task.run()


def register():
    pass


def unregister():
    pass
