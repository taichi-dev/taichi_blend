import numpy as np
from tina import *
import bpy


def to_flat_numpy(b, key, dim=None, dtype=None):
    expect_dim = len(getattr(b[0], key)) if len(b) else None
    if dim is None:
        dim = expect_dim
    elif expect_dim is not None:
        assert dim == expect_dim, f'dimension mismatch: {dim} != {expect_dim}'
    seq = [0] * (len(b) * dim)
    b.foreach_get(key, seq)
    return np.array(seq, dtype=dtype)


def from_flat_numpy(b, key, a, dim=None):
    if dim is None:
        dim = len(getattr(b[0], key))
    assert len(a.shape) == 1
    if len(b) < a.shape[0]:
        b.add(a.shape[0] - len(b))
    seq = a.tolist()  # bottleneck
    if len(seq) < len(b) * dim:
        seq = seq + [0] * (len(b) * dim - len(seq))
    b.foreach_set(key, seq)


def bmesh_verts_to_numpy(bm):
    arr = [x.co for x in bm.verts]
    if len(arr) == 0:
        print('Warning: no vertices!')
        return np.zeros((0, 3), dtype=np.float32)
    return np.array(arr, dtype=np.float32)


def bmesh_faces_to_numpy(bm):
    arr = [[y.index for y in x.verts] for x in bm.faces]
    if len(arr) == 0:
        print('Warning: no faces!')
        return np.zeros((0, 3), dtype=np.int32)
    return np.array(arr, dtype=np.int32)


def mesh_update(mesh, verts=None, edges=None, faces=None, npoly=None):
    if verts is not None:
        from_flat_numpy(mesh.vertices, 'co', verts, 3)
    if edges is not None:
        from_flat_numpy(mesh.edges, 'vertices', edges, 2)
    if faces is not None:
        from_flat_numpy(mesh.polygons, 'vertices', faces, npoly)
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
class InputMeshObject(IRun):
    '''
    Name: input_mesh_object
    Category: input
    Inputs: object:so maxverts:i npolygon:i maxfaces:i use_raw:b
    Output: verts:cf% faces:cf% update:t local:x%
    '''
    def __init__(self, name, maxverts, npolygon, maxfaces, use_raw=False):
        self.name = name
        self.use_raw = use_raw

        assert maxverts != 0
        self.verts = DynamicField(C.float(3)[maxverts])
        self.maxverts = maxverts

        assert npolygon != 0
        self.npolygon = npolygon

        assert maxfaces != 0
        self.faces = DynamicField(C.int(npolygon)[maxfaces])
        self.maxfaces = maxfaces

        self.local = IMatrix()

    def update_mesh(self, verts, faces):
        nverts = verts.shape[0] // 3
        if nverts > self.maxverts:
            raise ValueError(f'Please increase maxverts: {nverts} > {self.maxverts}')
        self._update(self.verts, verts, nverts, 3)

        nfaces = faces.shape[0] // self.npolygon
        if nfaces > self.maxfaces:
            raise ValueError(f'Please increase maxfaces: {nfaces} > {self.maxfaces}')
        self._update(self.faces, faces, nfaces, self.npolygon)

    def run(self):
        object = bpy.data.objects[self.name]

        if self.use_raw:
            mesh = object.data
            verts = to_flat_numpy(mesh.vertices, 'co', 3, np.float32)
            faces = to_flat_numpy(mesh.polygons, 'vertices', self.npolygon, np.int32)
            #verts = verts.reshape(len(mesh.vertices), 3)
            #faces = faces.reshape(len(mesh.vertices), self.npolygon)

        else:
            depsgraph = bpy.context.evaluated_depsgraph_get()

            import bmesh
            bm = bmesh.new()
            object_eval = object.evaluated_get(depsgraph)
            bm.from_object(object_eval, depsgraph)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            verts = bmesh_verts_to_numpy(bm)
            faces = bmesh_faces_to_numpy(bm)
            assert faces.shape[1] == self.npolygon, f'npolygon should be {faces.shape[1]}'
            verts = verts.reshape(verts.shape[0] * verts.shape[1])
            faces = faces.reshape(faces.shape[0] * faces.shape[1])

        self.update_mesh(verts, faces)

        local = np.array(object.matrix_local)
        self.local.matrix[None] = local.tolist()

    @ti.kernel
    def _update(self, self_verts: ti.template(),
            verts: ti.ext_arr(), nverts: int, dim: ti.template()):
        self_verts.size[None] = nverts
        for i in range(nverts):
            for j in ti.static(range(dim)):
                self_verts[i][j] = verts[i * dim + j]

    @ti.func
    def __iter__(self):
        for I in ti.grouped(ti.ndrange(self.nverts[None])):
            yield I


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
        return verts

    def run(self):
        frame = bpy.context.scene.frame_current
        frame = max(frame, bpy.context.scene.frame_start)
        frame = min(frame, bpy.context.scene.frame_end)
        frameid = frame - bpy.context.scene.frame_start

        while len(self.cache) <= frameid:
            frame = len(self.cache) + bpy.context.scene.frame_start
            mesh_name = f'{self.object.name}_{frame:03d}'
            verts = self.update_data()
            mesh = new_mesh(mesh_name)
            from_flat_numpy(mesh.vertices, 'co', verts, 3)
            mesh.update()
            self.cache.append(mesh_name)

        mesh_name = self.cache[frameid]
        object = bpy.data.objects[self.object.name]
        object.data = bpy.data.meshes[mesh_name]


@A.register
class RenderInputs(INode):
    '''
    Name: render_inputs
    Category: input
    Inputs:
    Output: pers:x% inv_pers:x% view:x% inv_view:x%
    '''
    def __init__(self):
        self.pers = IMatrix()
        self.inv_pers = IMatrix()
        self.view = IMatrix()
        self.inv_view = IMatrix()

    def set_region_data(self, region3d):
        pers = np.array(region3d.perspective_matrix)
        inv_pers = np.array(region3d.perspective_matrix.inverted())
        view = np.array(region3d.view_matrix)
        inv_view = np.array(region3d.view_matrix.inverted())

        self.pers.matrix[None] = pers.tolist()
        self.inv_pers.matrix[None] = inv_pers.tolist()
        self.view.matrix[None] = view.tolist()
        self.inv_view.matrix[None] = inv_view.tolist()


@A.register
class RenderOutput(INode):
    '''
    Name: render_output
    Category: output
    Inputs: image:vf update:t
    Output:
    '''
    def __init__(self, img, update):
        assert isinstance(img, IField)
        assert isinstance(update, IRun)

        self.img = img
        self.update = update

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

    def render(self, *args):
        self.update.run()
        self._render(*args)

    @ti.kernel
    def _render(self, out: ti.ext_arr(), width: int, height: int):
        for i, j in ti.ndrange(width, height):
            r, g, b = self.image_at(i, j, width, height)
            base = (j * width + i) * 4
            out[base + 0] = r
            out[base + 1] = g
            out[base + 2] = b
            out[base + 3] = 1

# TODO: fix CurrentFrame/DiskFrameCache for MeshSequence on skip frame

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
def Switch(alter, t, alt):
    '''
    Name: socket_switch
    Category: misc
    Inputs: alter:b t:a alt:a
    Output: out:a
    '''
    return alt if alter else t


@A.register
class ShowArray(IRun):
    '''
    Name: show_array
    Category: misc
    Inputs: field:f update:t
    Output: update:t
    '''

    def __init__(self, field, chain):
        super().__init__(chain)
        assert hasattr(field, 'to_numpy')

        self.field = field

    def _run(self):
        value = self.field.to_numpy()

        print(value)
        print('shape:', ', '.join(map(str, value.shape)))
        print('max:', value.max())
        print('min:', value.min())


def register():
    pass


def unregister():
    pass
