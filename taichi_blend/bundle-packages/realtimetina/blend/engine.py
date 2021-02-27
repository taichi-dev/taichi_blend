import bpy

from ..common import *
from ..advans import *
from .cache import IDCache


@ti.data_oriented
class OutputPixelConverter:
    def cook(self, color):
        if isinstance(color, ti.Expr):
            color = ti.Vector([color, color, color])
        elif isinstance(color, ti.Matrix):
            assert color.m == 1, color.m
            if color.n == 1:
                color = ti.Vector([color(0), color(0), color(0)])
            elif color.n == 2:
                color = ti.Vector([color(0), color(1), 0.])
            elif color.n in [3, 4]:
                color = ti.Vector([color(0), color(1), color(2)])
            else:
                assert False, color.n
        return color

    @ti.func
    def dump_body(self, img: ti.template(), use_bilerp: ti.template(),
            is_final: ti.template(), out: ti.template(), i, j, width, height):
        color = V(0., 0., 0.)
        if ti.static(use_bilerp):
            scale = ti.Vector(img.shape) / ti.Vector([width, height])
            pos = ti.Vector([i, j]) * scale
            color = bilerp(img, pos)
        else:
            color = img[i, j]
        color = aces_tonemap(color)
        if ti.static(is_final):
            base = (j * width + i) * 4
            out[base + 0] = color.x
            out[base + 1] = color.y
            out[base + 2] = color.z
            out[base + 3] = 1
        else:
            out[j * width + i] = self.rgb24(color)

    @ti.kernel
    def dump(self, img: ti.template(), use_bilerp: ti.template(),
            is_final: ti.template(), out: ti.ext_arr(), width: int, height: int):
        for ii, jj in ti.ndrange(img.shape[0], img.shape[1]):
            if ti.static(not use_bilerp):
                self.dump_body(img, False, is_final, out, ii, jj, width, height)
            else:
                j = jj
                while True:
                    if j >= height:
                        break
                    i = ii
                    while True:
                        if i >= width:
                            break
                        self.dump_body(img, True, is_final, out, i, j, width, height)
                        i += img.shape[0]
                    j += img.shape[1]

    @staticmethod
    @ti.func
    def rgb24(color):
        r, g, b = clamp(int(color * 255 + 0.5), 0, 255)
        return (b << 16) + (g << 8) + r


def get_material_from_node_group(node_group_name):
    from melt.blender import get_node_table

    node_group = bpy.data.node_groups[node_group_name]
    node_table = get_node_table(node_group)
    material_output = node_table['Material Output']

    return material_output


class BlenderEngine(tina.Engine):
    def make_shader_of_object(self, object):
        if not object.tina_material_nodes:
            return None
        material = get_material_from_node_group(object.tina_material_nodes)
        shader = tina.Shader(self.color, self.lighting, material)
        return shader

    def __init__(self):
        super().__init__((
            bpy.context.scene.tina_resolution_x,
            bpy.context.scene.tina_resolution_y),
            bpy.context.scene.tina_max_faces,
            bpy.context.scene.tina_smoothing,
            bpy.context.scene.tina_texturing,
            bpy.context.scene.tina_culling,
            bpy.context.scene.tina_clipping)

        self.output = OutputPixelConverter()
        self.cache = IDCache(lambda o: (type(o).__name__, o.name))

        self.camera = tina.Camera()
        self.accum = tina.Accumator(self.res)
        self.lighting = tina.Lighting(bpy.context.scene.tina_max_lights)
        self.color = ti.Vector.field(3, float, self.res)

        self.default_shader = tina.Shader(self.color, self.lighting,
                tina.BlinnPhong())
        self.shaders = {}
        for object in bpy.context.scene.objects:
            shader = self.make_shader_of_object(object)
            if shader is not None:
                self.shaders[object.name] = shader

    def render_scene(self, is_final):
        is_center = False
        if not is_final:
            if self.accum.count[None] == 0:
                is_center = True
            if bpy.context.scene.tina_viewport_samples == 1:
                is_center = True
        self.randomize_bias(is_center)
        self.clear_depth()
        self.color.fill(0)

        lights = []
        meshes = []

        for object in bpy.context.scene.objects:
            if not object.visible_get():
                continue
            if object.type == 'LIGHT':
                lights.append(object)
            if object.type == 'MESH':
                meshes.append(object)

        self.lighting.nlights[None] = len(lights)
        for i, object in enumerate(lights):
            self.update_light(i, object)

        for object in meshes:
            self.render_object(object)

        if is_final or bpy.context.scene.tina_viewport_samples != 1:
            self.accum.update(self.color)

    def clear_samples(self):
        if bpy.context.scene.tina_viewport_samples != 1:
            self.accum.clear()
        else:
            self.accum.count[None] = 0

    def is_need_redraw(self):
        return self.accum.count[None] < bpy.context.scene.tina_viewport_samples

    def update_light(self, i, object):
        color = np.array(object.data.color) * object.data.energy / 4
        model = np.array(object.matrix_world)

        if object.data.type == 'SUN':
            dir = model @ np.array([0, 0, 1, 0])
        elif object.data.type == 'POINT':
            dir = model @ np.array([0, 0, 0, 1])
            dir[3] = 1
            color /= 12
        else:
            assert False, f'unsupported light type: {object.data.type}'

        self.lighting.light_dirs[i] = dir.tolist()
        self.lighting.light_colors[i] = color.tolist()

    def render_object(self, object):
        verts, norms, coors = self.cache.lookup(blender_get_object_mesh, object)
        if not len(verts):
            return

        shader = self.shaders.get(object.name, self.default_shader)

        self.camera.model = np.array(object.matrix_world)
        self.set_camera(self.camera)

        self.set_face_verts(verts)
        if self.smoothing:
            self.set_face_norms(norms)
        if self.texturing:
            self.set_face_coors(coors)
        self.render(shader)

    def update_region_data(self, region3d):
        pers = np.array(region3d.perspective_matrix)
        self.camera.view = np.array(region3d.view_matrix)
        self.camera.proj = pers @ np.linalg.inv(self.camera.view)

    def update_default_camera(self):
        camera = bpy.context.scene.camera
        render = bpy.context.scene.render
        depsgraph = bpy.context.evaluated_depsgraph_get()
        scale = render.resolution_percentage / 100.0
        self.camera.proj = np.array(camera.calc_matrix_camera(depsgraph,
            x=render.resolution_x * scale, y=render.resolution_y * scale,
            scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y))
        self.camera.view = np.linalg.inv(np.array(camera.matrix_world))

    def dump_pixels(self, pixels, width, height, is_final):
        use_bilerp = not (width == self.res.x and height == self.res.y)
        if is_final or bpy.context.scene.tina_viewport_samples != 1:
            self.output.dump(self.accum.img, use_bilerp, is_final, pixels, width, height)
        else:
            self.output.dump(self.color, use_bilerp, is_final, pixels, width, height)

    def invalidate_callback(self, update):
        object = update.id
        if update.is_updated_geometry:
            self.cache.invalidate(object)


def bmesh_verts_to_numpy(bm):
    arr = [x.co for x in bm.verts]
    if len(arr) == 0:
        return np.zeros((0, 3), dtype=np.float32)
    return np.array(arr, dtype=np.float32)


def bmesh_faces_to_numpy(bm):
    arr = [[e.index for e in f.verts] for f in bm.faces]
    if len(arr) == 0:
        return np.zeros((0, 3), dtype=np.int32)
    return np.array(arr, dtype=np.int32)


def bmesh_face_norms_to_numpy(bm):
    vnorms = [x.normal for x in bm.verts]
    if len(vnorms) == 0:
        vnorms = np.zeros((0, 3), dtype=np.float32)
    else:
        vnorms = np.array(vnorms)
    norms = [
        [vnorms[e.index] for e in f.verts]
        if f.smooth else [f.normal for e in f.verts]
        for f in bm.faces]
    if len(norms) == 0:
        return np.zeros((0, 3, 3), dtype=np.float32)
    return np.array(norms, dtype=np.float32)


def bmesh_face_coors_to_numpy(bm):
    uv_lay = bm.loops.layers.uv.active
    if uv_lay is None:
        return np.zeros((len(bm.faces), 3, 2), dtype=np.float32)
    coors = [[l[uv_lay].uv for l in f.loops] for f in bm.faces]
    if len(coors) == 0:
        return np.zeros((0, 3, 2), dtype=np.float32)
    return np.array(coors, dtype=np.float32)


def blender_get_object_mesh(object):
    import bmesh
    bm = bmesh.new()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = object.evaluated_get(depsgraph)
    bm.from_object(object_eval, depsgraph)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    verts = bmesh_verts_to_numpy(bm)[bmesh_faces_to_numpy(bm)]
    norms = bmesh_face_norms_to_numpy(bm)
    coors = bmesh_face_coors_to_numpy(bm)
    return verts, norms, coors
