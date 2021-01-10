from . import *

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
class InputObjectMesh(IRun):
    '''
    Name: input_object_mesh
    Category: input
    Inputs: object:so maxverts:i maxfaces:i npolygon:i use_raw:b
    Output: verts:vf% faces:vf% update:t
    '''
    def __init__(self, name, maxverts, maxfaces, npolygon, use_raw=False):
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
    Inputs: object:a update:t verts:vf faces:vf
    Output: update:t
    '''
    def __init__(self, object, update, verts, faces):
        assert isinstance(object, NewMeshObject)
        assert isinstance(update, IRun)
        assert isinstance(verts, IField)
        assert faces is None or isinstance(faces, IField)

        #faces = A.field_storage(C.int(3)[1])
        #ti.materialize_callback(lambda: faces.from_numpy(np.array([[0, 1, 2]], dtype=np.int32)))
        self.verts = verts
        self.faces = faces
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

        if hasattr(self.verts, 'get_length'):
            length = self.verts.get_length()
        else:
            assert len(self.verts.meta.shape) == 1, 'please use A.flatten_field'
            length = self.verts.meta.shape[0]
        verts = np.empty(length * 3)
        export_vfield(self.verts, verts, 3)
        verts = verts.reshape(len(verts) // 3, 3)

        if self.faces is not None:
            if hasattr(self.faces, 'get_length'):
                length = self.faces.get_length()
            else:
                assert len(self.faces.meta.shape) == 1, 'please use A.flatten_field'
                length = self.faces.meta.shape[0]
            faces = np.empty(length * 3)
            export_vfield(self.faces, faces, 3)
            faces = faces.reshape(len(faces) // 3, 3)
        else:
            faces = None

        return verts, faces

    def run(self):
        frame = bpy.context.scene.frame_current
        frame = max(frame, bpy.context.scene.frame_start)
        frame = min(frame, bpy.context.scene.frame_end)
        frameid = frame - bpy.context.scene.frame_start

        while len(self.cache) <= frameid:
            frame = len(self.cache) + bpy.context.scene.frame_start
            mesh_name = f'{self.object.name}_{frame:03d}'
            verts, faces = self.update_data()
            mesh = new_mesh(mesh_name, verts, None, faces)
            mesh.update()
            self.cache.append(mesh_name)

        mesh_name = self.cache[frameid]
        object = bpy.data.objects[self.object.name]
        object.data = bpy.data.meshes[mesh_name]


# TODO: fix CurrentFrameId/DiskFrameCache for MeshSequence on skip frame
@A.register
class CurrentFrameId(A.uniform_field, IRun):
    '''
    Name: current_frame_id
    Category: blender
    Inputs:
    Output: frame:f update:t
    '''

    def __init__(self):
        super().__init__(Field(Meta([], int, [])))

    def run(self):
        self.value[None] = bpy.context.scene.frame_current


@A.register
def OutputMeshAnimation(target, preserve, verts, faces, start, update):
    '''
    Name: output_mesh_animation
    Category: output
    Inputs: target:so preserve:b verts:vf faces:vf start:t update:t
    Output:
    '''

    object = NewMeshObject(target, preserve)
    start = A.merge_tasks(object, start)
    update = MeshSequence(object, update, verts, faces)
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
def FVConst3(coors):
    '''
    Name: const_vector_field
    Category: sampler
    Inputs: coors:c3
    Output: vector:vf
    '''

    return A.const_field(V(*coors))


@A.register
def FVUnpack(vec):
    '''
    Name: unpack_vector
    Category: converter
    Inputs: vector:vf
    Output: x:f% y:f% z:f% w:f%
    '''

    return vec


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


def get_node_table(node_group):
    def get_table(node_group):
        nodes = []
        for key, node in node_group.nodes.items():
            inputs = []
            options = []
            for (opt_name, opt_type), opt_id in node.ns_options:
                if opt_name in node:
                    item = node[opt_name]
                else:
                    if opt_type == 'str' or opt_type.startswith('search_'):
                        item = ''
                    elif opt_type.startswith('vec_'):
                        item = (0,) * int(opt_type.split('_')[-1])
                    else:
                        item = 0
                if opt_type == 'enum':
                    item = node.ns_option_items[opt_id][item]
                elif opt_type.startswith('vec_'):
                    item = tuple(item[i] for i in range(len(item)))
                options.append(item)
            for name, socket in node.inputs.items():
                link_node = None
                link_socket = 0
                if len(socket.links):
                    link_node = socket.links[0].from_node
                    link_socket = socket.links[0].from_socket
                    link_socket = list(link_node.outputs).index(link_socket)
                    link_node = node_group.nodes.keys().index(link_node.name)
                inputs.append((link_node, link_socket))
            ninfo = node.ns_wrapped, node.name, tuple(inputs), tuple(options)
            nodes.append(ninfo)
        return nodes


    def construct_table(nodes):
        visited = [None for i in nodes]
        entered = [False for i in nodes]

        def dfs(i):
            if i is None:
                return None, [None]

            assert not entered[i], i
            if visited[i] is not None:
                return visited[i]

            entered[i] = True
            cons, name, inputs, options = nodes[i]
            args = []
            for j, k in inputs:
                ret, rets = dfs(j)
                args.append(rets[k])

            res = cons(tuple(args), options)
            visited[i] = res
            entered[i] = False
            return res

        for i in range(len(nodes)):
            dfs(i)

        table = {}
        for i, ninfo in enumerate(nodes):
            name = ninfo[1]
            ret, rets = visited[i]
            table[name] = ret
        return table

    return construct_table(get_table(node_group))
