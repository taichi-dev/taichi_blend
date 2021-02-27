'''
Blender intergration module

references: https://docs.blender.org/api/current/bpy.types.RenderEngine.html
'''

import bpy
import bgl
import time
import numpy as np


if 1:
    from tina.tools import mtworker
    @mtworker.OnDemandProxy
    def worker():
        @mtworker.DaemonModule
        def worker():
            print('[TinaBlend] importing worker')
            if 1:
                from tina import worker
            else:
                from scripts import dummy_worker as worker
            print('[TinaBlend] importing worker done')
            return worker

        print('[TinaBlend] initializing worker')
        worker.init()
        print('[TinaBlend] initializing worker done')

        return worker
else:
    from tina import worker
    worker.init()


def calc_camera_matrices(depsgraph):
    camera = depsgraph.scene.camera
    render = depsgraph.scene.render
    scale = render.resolution_percentage / 100.0
    proj = np.array(camera.calc_matrix_camera(depsgraph,
        x=render.resolution_x * scale, y=render.resolution_y * scale,
        scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y))
    view = np.linalg.inv(np.array(camera.matrix_world))
    return view, proj


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


def blender_get_object_mesh(object, depsgraph=None):
    import bmesh
    bm = bmesh.new()
    if depsgraph is None:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = object.evaluated_get(depsgraph)
    bm.from_object(object_eval, depsgraph)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    verts = bmesh_verts_to_numpy(bm)[bmesh_faces_to_numpy(bm)]
    norms = bmesh_face_norms_to_numpy(bm)
    coors = bmesh_face_coors_to_numpy(bm)
    return verts, norms, coors


def blender_get_image_pixels(image):
    arr = np.array(image.pixels)
    arr = arr.reshape((image.size[1], image.size[0], image.channels))
    arr = arr.swapaxes(0, 1)
    if image.colorspace_settings.name == 'sRGB':
        arr = arr**2.2
    return arr


class TinaLightPanel(bpy.types.Panel):
    '''Tina light options'''

    COMPAT_ENGINES = {"TINA"}
    bl_label = 'Tina Light'
    bl_idname = 'DATA_PT_tina'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def draw(self, context):
        layout = self.layout
        object = context.object

        if object.type == 'LIGHT':
            layout.prop(object.data, 'color')
            layout.prop(object.data, 'energy')
            if object.data.type == 'POINT':
                layout.prop(object.data, 'shadow_soft_size', text='Radius')
            elif object.data.type == 'AREA':
                layout.prop(object.data, 'size')


class TinaRenderPanel(bpy.types.Panel):
    '''Tina render options'''

    COMPAT_ENGINES = {"TINA"}
    bl_label = 'Tina Render'
    bl_idname = 'RENDER_PT_tina'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout
        options = context.scene.tina_render

        layout.prop(options, 'render_samples')
        layout.prop(options, 'viewport_samples')
        layout.prop(options, 'albedo_samples')
        layout.prop(options, 'start_pixel_size')
        layout.prop(options, 'pixel_scale')
        layout.prop(options, 'update_interval')
        layout.prop(options, 'sync_interval')
        #layout.prop(options, 'mlt_lsp')
        #layout.prop(options, 'mlt_sigma')


class TinaWorldPanel(bpy.types.Panel):
    '''Tina world options'''

    COMPAT_ENGINES = {"TINA"}

    bl_label = 'Tina World'
    bl_idname = 'WORLD_PT_tina'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'world'

    def draw(self, context):
        layout = self.layout
        world = context.scene.world


# {{{
class TinaMaterialPanel(bpy.types.Panel):
    '''Tina material options'''

    COMPAT_ENGINES = {"TINA"}
    bl_label = 'Tina Material'
    bl_idname = 'MATERIAL_PT_tina'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    def draw(self, context):
        layout = self.layout

        material = context.object.active_material
        if not material:
            return
        options = material.tina

        layout.prop(options, 'basecolor')
        layout.prop(options, 'basecolor_texture')
        layout.prop(options, 'metallic')
        layout.prop(options, 'metallic_texture')
        layout.prop(options, 'roughness')
        layout.prop(options, 'roughness_texture')
        layout.prop(options, 'specular')
        layout.prop(options, 'specularTint')
        layout.prop(options, 'subsurface')
        layout.prop(options, 'sheen')
        layout.prop(options, 'sheenTint')
        layout.prop(options, 'clearcoat')
        layout.prop(options, 'clearcoatGloss')
        layout.prop(options, 'transmission')
        layout.prop(options, 'ior')


from bl_ui.space_node import NODE_HT_header
from bl_ui.properties_material import MaterialButtonsPanel


class TINA_PT_context_material(MaterialButtonsPanel, bpy.types.Panel):
    """
    Material UI Panel
    """
    COMPAT_ENGINES = {"TINA"}
    bl_label = ""
    bl_options = {"HIDE_HEADER"}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine == "TINA")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        obj = context.object
        slot = context.material_slot
        space = context.space_data

        # Re-create the Blender material UI, but without the surface/wire/volume/halo buttons
        if obj:
            is_sortable = len(obj.material_slots) > 1
            rows = 1
            if (is_sortable):
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if obj.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        row = layout.row()
        if obj:
            row.template_ID(obj, 'active_material', new='material.new')
            if slot:
                icon_link = 'MESH_DATA' if slot.link == 'DATA' else 'OBJECT_DATA'
                row.prop(slot, 'link', icon=icon_link, icon_only=True)
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()
# }}}


class TinaRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "TINA"
    bl_label = "Tina"
    bl_use_preview = False

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):
        self.scene_data = None
        self.draw_data = None
        self.closed_draws = []
        self.waiting = False

        self.object_to_mesh = {}
        self.object_to_light = {}
        self.ui_materials = []
        self.materials = []
        self.ui_images = []
        self.images = []
        self.world_light = None
        self.nblocks = 0
        self.nsamples = 0

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        pass

    def __add_mesh_object(self, object, depsgraph):
        print('[TinaBlend] adding mesh object', object.name)

        verts, norms, coors = blender_get_object_mesh(object, depsgraph)
        world = np.array(object.matrix_world)

        mtlid = -1
        if object.active_material:
            name = object.active_material.name
            if name in self.ui_materials:
                mtlid = self.ui_materials.index(name)
                print('[TinaBlend] material', name, 'has id', mtlid)
            else:
                print('[TinaBlend] material', name, 'not found!')

        self.object_to_mesh[object] = world, verts, norms, coors, mtlid

    def __add_light_object(self, object, depsgraph):
        print('[TinaBlend] adding light object', object.name)

        world = np.array(object.matrix_world)
        color = np.array(object.data.color)
        color *= object.data.energy
        type = object.data.type

        if type == 'POINT':
            size = max(object.data.shadow_soft_size, 1e-6)
            color /= size**2
            color *= 0.0257065145620267
        elif type == 'AREA':
            assert object.data.shape == 'SQUARE'
            size = max(object.data.size / 2, 1e-6)
            color /= size**2
            color *= 0.06275642352999936
        else:
            raise ValueError(type)

        self.object_to_light[object] = world, color, size, type

    def __add_image(self, image):
        print('[TinaBlend] adding image', image.name)

        name = image.name
        image = blender_get_image_pixels(image)

        if name not in self.ui_images:
            self.ui_images.append(name)
            self.images.append(image)
        else:
            texid = self.ui_images.index(name)
            self.images[texid] = image

    def __get_image_id(self, image):
        if image is not None:
            self.__add_image(image)
            if image.name in self.ui_images:
                return self.ui_images.index(image.name)
        return -1
        # import code; code.interact(local=locals())

    def __add_world(self, world, depsgraph):
        print('[TinaBlend] adding world', world.name)

        tree = world.node_tree

        def get_input(node, name):
            input = node.inputs[name]
            if input.is_linked:
                return input.links[0].from_node
            else:
                value = input.default_value
                return value

        output = tree.nodes['World Output']
        bsdf = get_input(output, 'Surface')
        if not isinstance(bsdf, bpy.types.ShaderNodeBackground):
            raise RuntimeError('only `Background` node is supported for now')

        def parse_value(value):
            if isinstance(value, bpy.types.ShaderNodeTexEnvironment):
                factor = [1.0] * 4
                texture = self.__get_image_id(value.image)
            elif isinstance(value, bpy.types.ShaderNode):
                raise RuntimeError('shader nodes other than environment texture '
                        'are not supported for now')
            else:
                if hasattr(value, '__iter__'):
                    factor = list(value)
                else:
                    factor = [value] * 4
                texture = -1
            return factor, texture

        factor, texture = parse_value(get_input(bsdf, 'Color'))
        strength = get_input(bsdf, 'Strength')
        if isinstance(strength, bpy.types.ShaderNode):
            raise RuntimeError('strength socket does not support texture for now')
        strength = float(strength)
        factor = [x * strength for x in factor]

        self.world_light = factor, texture

    def __parse_material(self, material):
        tree = material.node_tree

        def get_input(node, name):
            input = node.inputs[name]
            if input.is_linked:
                return input.links[0].from_node
            else:
                value = input.default_value
                return value

        output = tree.nodes['Material Output']
        bsdf = get_input(output, 'Surface')
        if not isinstance(bsdf, bpy.types.ShaderNodeBsdfPrincipled):
            raise RuntimeError('only `Principled BSDF` is supported for now')

        def parse_value(value):
            if isinstance(value, bpy.types.ShaderNodeTexImage):
                factor = [1.0] * 4
                texture = self.__get_image_id(value.image)
            elif isinstance(value, bpy.types.ShaderNode):
                raise RuntimeError('shader nodes other than image texture '
                        'are not supported for now')
            else:
                if hasattr(value, '__iter__'):
                    factor = list(value)
                else:
                    factor = [value] * 4
                texture = -1
            return factor, texture

        def parse_input(name):
            value = get_input(bsdf, name)
            return parse_value(value)

        return (
            parse_input('Base Color'),
            parse_input('Metallic'),
            parse_input('Roughness'),
            parse_input('Specular'),
            parse_input('Specular Tint'),
            parse_input('Subsurface'),
            parse_input('Sheen'),
            parse_input('Sheen Tint'),
            parse_input('Clearcoat'),
            parse_input('Clearcoat Roughness'),
            parse_input('Transmission'),
            parse_input('IOR'),
            )

    def __add_material(self, material, depsgraph):
        print('[TinaBlend] adding material', material.name)

        name = material.name
        material = self.__parse_material(material)

        if name not in self.ui_materials:
            self.ui_materials.append(name)
            self.materials.append(material)
        else:
            mtlid = self.ui_materials.index(name)
            self.materials[mtlid] = material

    def __setup_scene(self, depsgraph):
        print('[TinaBlend] setup scene')

        scene = depsgraph.scene
        options = scene.tina_render

        for object in depsgraph.ids:
            if isinstance(object, bpy.types.Material):
                self.__add_material(object, depsgraph)

            if isinstance(object, bpy.types.World):
                if scene.world.name == object.name:
                    self.__add_world(object, depsgraph)

        for object in depsgraph.ids:
            if isinstance(object, bpy.types.Object):
                if object.type == 'MESH':
                    self.__add_mesh_object(object, depsgraph)
                elif object.type == 'LIGHT':
                    self.__add_light_object(object, depsgraph)

        self.__on_update(depsgraph)

    def __update_scene(self, depsgraph):
        print('[TinaBlend] update scene')

        scene = depsgraph.scene

        need_update = False

        for update in depsgraph.updates:
            object = update.id

            if isinstance(object, bpy.types.Material):
                self.__add_material(object, depsgraph)
                need_update = True

            if isinstance(object, bpy.types.World):
                if scene.world.name == object.name:
                    self.__add_world(object, depsgraph)
                    need_update = True

        for update in depsgraph.updates:
            object = update.id

            if isinstance(object, bpy.types.Scene):
                obj_to_del = []
                for obj in self.object_to_mesh:
                    if obj.name not in object.objects:
                        print('[TinaBlend] removing mesh object', obj)
                        obj_to_del.append(obj)
                for obj in obj_to_del:
                    del self.object_to_mesh[obj]
                    need_update = True

                obj_to_del = []
                for obj in self.object_to_light:
                    if obj.name not in object.objects:
                        print('[TinaBlend] removing light object', obj)
                        obj_to_del.append(obj)
                for obj in obj_to_del:
                    del self.object_to_light[obj]
                    need_update = True

            if isinstance(object, bpy.types.Object):
                if object.type == 'MESH':
                    self.__add_mesh_object(object, depsgraph)
                    need_update = True
                elif object.type == 'LIGHT':
                    self.__add_light_object(object, depsgraph)
                    need_update = True

        if need_update:
            self.update_stats('Initializing', 'Updating scene')

            self.__on_update(depsgraph)

    def __on_update(self, depsgraph):
        self.update_stats('Initializing', 'Composing meshes')
        meshes = []
        for world, verts, norms, coors, mtlid in self.object_to_mesh.values():
            meshes.append((verts, norms, coors, world, mtlid))

        from tina.multimesh import compose_multiple_meshes
        vertices, mtlids = compose_multiple_meshes(meshes)

        self.update_stats('Initializing', 'Loading materials')
        worker.load_materials(self.materials)
        self.update_stats('Initializing', 'Loading images')
        worker.load_images(self.images)
        self.update_stats('Initializing', 'Loading models')
        worker.load_model(vertices, mtlids)
        self.update_stats('Initializing', 'Constructing tree')
        worker.build_tree()

        self.update_stats('Initializing', 'Updating world light')
        if self.world_light is not None:
            worker.set_world_light(*self.world_light)

        self.update_stats('Initializing', 'Updating lights')
        worker.clear_lights()
        for world, color, size, type in self.object_to_light.values():
            worker.add_light(world, color, size, type)

        self.__reset_samples(depsgraph.scene)

    def __reset_samples(self, scene):
        options = scene.tina_render
        #worker.set_mlt_param(options.mlt_lsp, options.mlt_sigma)

        self.nsamples = 0
        self.nblocks = scene.tina_render.start_pixel_size

    render_passes = [
        ('Combined', 'RGBA', 'COLOR'),
        ('Albedo', 'RGB', 'COLOR'),
        ('Normal', 'XYZ', 'VECTOR'),
    ]

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        for name, channels, type in self.render_passes:
            if name not in ['Combined', 'Depth']:
                self.add_pass(name, len(channels), channels)

        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)
        view, proj = calc_camera_matrices(depsgraph)

        self.update_stats('Initializing', 'Loading scene')

        self.__setup_scene(depsgraph)
        self.__update_camera(proj @ view)
        worker.set_size(self.size_x, self.size_y)

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0]

        for id in range(len(self.render_passes)):
            worker.clear(id)

        t0 = time.time()
        interval = scene.tina_render.update_interval
        sync_interval = scene.tina_render.sync_interval

        nsamples = scene.tina_render.render_samples
        for samp in range(nsamples):
            self.update_stats('Rendering', f'{samp}/{nsamples} Samples')
            self.update_progress((samp + .5) / nsamples)
            if self.test_break():
                break

            worker.render()
            if samp < scene.tina_render.albedo_samples:
                worker.render_preview()

            if samp % sync_interval == sync_interval - 1:
                print('[TinaBlend] synchronizing device...')
                worker.synchronize()

            do_update = time.time() - t0 > interval

            if do_update or samp == 0 or samp == nsamples - 1:
                print('[TinaBlend] updating film at', samp, 'samples')
                for id, (name, channels, type) in enumerate(self.render_passes):
                    img = worker.get_image(id)
                    img = np.ascontiguousarray(img.swapaxes(0, 1))
                    img = img.reshape(self.size_x * self.size_y, 4)
                    if len(channels) != 4:
                        img = img[:, :len(channels)]
                    layer.passes[name].rect = img.tolist()

                self.update_result(result)
                t0 = time.time()

        else:
            self.update_progress(1.0)

        self.end_result(result)

    def update_render_passes(self, scene=None, renderlayer=None):
        for name, channels, type in self.render_passes:
            self.register_pass(scene, renderlayer,
                    name, len(channels), channels, type)

    def __update_camera(self, perspective):
        worker.set_camera(np.array(perspective))

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph):
        print('[TinaBlend] view_update')

        region = context.region
        region3d = context.region_data
        view3d = context.space_data
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height
        perspective = region3d.perspective_matrix.to_4x4()
        self.size_x, self.size_y = dimensions

        if not self.scene_data:
            # First time initialization
            self.scene_data = True
            first_time = True

            # Loop over all datablocks used in the scene.
            self.__setup_scene(depsgraph)
            self.__update_camera(perspective)
        else:
            first_time = False

            # Test which datablocks changed
            for update in depsgraph.updates:
                print("Datablock updated:", update.id.name)

            self.__update_scene(depsgraph)

            # Test if any material was added, removed or changed.
            if depsgraph.id_type_updated('MATERIAL'):
                print('[TinaBlend] Materials updated')

        # Loop over all object instances in the scene.
        if first_time or depsgraph.id_type_updated('OBJECT'):
            for instance in depsgraph.object_instances:
                pass

    def my_draw(self, context, depsgraph):
        if self.waiting:
            print('[TinaBlend] draw data busy')
            return
        self.waiting = True

        region = context.region
        region3d = context.region_data
        view3d = context.space_data
        scene = depsgraph.scene
        max_samples = scene.tina_render.viewport_samples
        pixel_scale = scene.tina_render.pixel_scale

        is_preview = view3d.shading.type == 'MATERIAL'

        # Get viewport dimensions
        dimensions = region.width, region.height
        perspective = region3d.perspective_matrix.to_4x4()

        if not self.draw_data or self.draw_data.dimensions != dimensions \
                or self.draw_data.is_preview != is_preview \
                or self.nblocks != 0:
            width, height = dimensions
            if self.nblocks != 0:
                width //= self.nblocks
                height //= self.nblocks
            if pixel_scale != 0:
                width //= pixel_scale
                height //= pixel_scale
            worker.set_size(width, height)

        if not self.draw_data or self.draw_data.dimensions != dimensions \
                or self.draw_data.is_preview != is_preview \
                or self.draw_data.perspective != perspective:
            self.__reset_samples(scene)
            self.__update_camera(perspective)

        if self.nsamples < max_samples:
            if self.nblocks > 1:
                self.nsamples = 0
                worker.clear(1 if is_preview else 0)
            else:
                if self.nblocks == 1:
                    worker.clear(1 if is_preview else 0)
                self.nsamples += 1

            self.update_stats('Rendering', f'{self.nsamples}/{max_samples} Samples')

            render = worker.render_preview if is_preview else worker.render
            do_tag_redraw = self.nsamples < max_samples or self.nblocks != 0
            self.nblocks //= 2

            @mtworker.DaemonThread
            def waiter():
                print('[TinaBlend] rendering draw data')
                render()
                print('[TinaBlend] updating draw data')
                draw_data = TinaDrawData(dimensions, perspective, is_preview)
                if self.draw_data:
                    self.draw_data, draw_data = draw_data, self.draw_data
                    self.closed_draws.append(draw_data)
                else:
                    self.draw_data = draw_data
                self.waiting = False
                if do_tag_redraw:
                    self.tag_redraw()

            waiter.start()

        else:
            self.waiting = False

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.
    def view_draw(self, context, depsgraph):
        print('[TinaBlend] view_draw')
        self.my_draw(context, depsgraph)

        scene = depsgraph.scene
        # Bind shader that converts from scene linear to display space,
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
        self.bind_display_space_shader(scene)
        while self.closed_draws:
            self.closed_draws.pop(0).close()
        if self.draw_data:
            self.draw_data.draw()
        else:
            print('[TinaBlend] no draw data, please wait')
        self.unbind_display_space_shader()
        bgl.glDisable(bgl.GL_BLEND)


class TinaDrawData:
    def __init__(self, dimensions, perspective, is_preview):
        self.initialized = False
        # Generate dummy float image buffer
        self.dimensions = dimensions
        self.perspective = perspective
        self.is_preview = is_preview
        width, height = dimensions

        self.resx, self.resy = worker.get_size()
        self.pixels_np = np.empty(self.resx * self.resy * 3, np.float32)
        worker.fast_export_image(self.pixels_np, 1 if is_preview else 0)

    def try_initialize(self):
        if self.initialized:
            return

        self.initialized = True

        resx, resy = self.resx, self.resy
        width, height = self.dimensions
        self.pixels = bgl.Buffer(bgl.GL_FLOAT, resx * resy * 3, self.pixels_np)

        # Generate texture
        self.texture = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, self.texture)
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture[0])
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, bgl.GL_RGB16F, resx, resy, 0, bgl.GL_RGB, bgl.GL_FLOAT, self.pixels)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)

        # Bind shader that converts from scene linear to display space,
        # use the scene's color management settings.
        shader_program = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGetIntegerv(bgl.GL_CURRENT_PROGRAM, shader_program)

        # Generate vertex array
        self.vertex_array = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenVertexArrays(1, self.vertex_array)
        bgl.glBindVertexArray(self.vertex_array[0])

        texturecoord_location = bgl.glGetAttribLocation(shader_program[0], "texCoord")
        position_location = bgl.glGetAttribLocation(shader_program[0], "pos")

        bgl.glEnableVertexAttribArray(texturecoord_location)
        bgl.glEnableVertexAttribArray(position_location)

        # Generate geometry buffers for drawing textured quad
        position = [0.0, 0.0, width, 0.0, width, height, 0.0, height]
        position = bgl.Buffer(bgl.GL_FLOAT, len(position), position)
        texcoord = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        texcoord = bgl.Buffer(bgl.GL_FLOAT, len(texcoord), texcoord)

        self.vertex_buffer = bgl.Buffer(bgl.GL_INT, 2)

        bgl.glGenBuffers(2, self.vertex_buffer)
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vertex_buffer[0])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, position, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(position_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.vertex_buffer[1])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, texcoord, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(texturecoord_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, 0)
        bgl.glBindVertexArray(0)

    def close(self):
        if not self.initialized:
            return

        bgl.glDeleteBuffers(2, self.vertex_buffer)
        bgl.glDeleteVertexArrays(1, self.vertex_array)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)
        bgl.glDeleteTextures(1, self.texture)

    def draw(self):
        self.try_initialize()
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.texture[0])
        bgl.glBindVertexArray(self.vertex_array[0])
        bgl.glDrawArrays(bgl.GL_TRIANGLE_FAN, 0, 4)
        bgl.glBindVertexArray(0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)


# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
        'VIEWLAYER_PT_filter',
        'VIEWLAYER_PT_layer_passes',
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if not hasattr(panel, 'COMPAT_ENGINES'):
            continue
        if 'CYCLES' not in panel.COMPAT_ENGINES:
            continue
        if panel.__name__ in exclude_panels:
            continue
        panels.append(panel)

    return panels


class TinaRenderProperties(bpy.types.PropertyGroup):
    render_samples: bpy.props.IntProperty(name='Render Samples', min=1, default=128)
    viewport_samples: bpy.props.IntProperty(name='Viewport Samples', min=1, default=32)
    albedo_samples: bpy.props.IntProperty(name='Albedo Samples', min=0, default=0)
    start_pixel_size: bpy.props.IntProperty(name='Start Pixel Size', min=1, default=16, subtype='PIXEL')
    pixel_scale: bpy.props.IntProperty(name='Pixel Scale', min=1, default=1, subtype='PIXEL')
    update_interval: bpy.props.FloatProperty(name='Update Interval', min=0, default=10, subtype='TIME')
    sync_interval: bpy.props.IntProperty(name='Synchronize Interval', min=1, default=4)
    #mlt_lsp: bpy.props.FloatProperty(name='MLT Large Step Probability', min=0, max=1, step=1, default=0.25)
    #mlt_sigma: bpy.props.FloatProperty(name='MLT Mutation Size', min=0, max=1, step=1, default=0.01)


def register():
    bpy.utils.register_class(TinaRenderProperties)

    bpy.types.Scene.tina_render = bpy.props.PointerProperty(name='tina', type=TinaRenderProperties)

    bpy.utils.register_class(TinaRenderEngine)
    #bpy.utils.register_class(TinaLightPanel)
    bpy.utils.register_class(TinaRenderPanel)
    #bpy.utils.register_class(TinaWorldPanel)
    #bpy.utils.register_class(TinaMaterialPanel)
    #bpy.utils.register_class(TINA_PT_context_material)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('TINA')


def unregister():
    bpy.utils.unregister_class(TinaRenderEngine)
    #bpy.utils.unregister_class(TinaLightPanel)
    bpy.utils.unregister_class(TinaRenderPanel)
    #bpy.utils.unregister_class(TinaWorldPanel)
    #bpy.utils.unregister_class(TinaMaterialPanel)
    #bpy.utils.unregister_class(TINA_PT_context_material)

    for panel in get_panels():
        if 'TINA' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('TINA')

    del bpy.types.Scene.tina_render

    bpy.utils.unregister_class(TinaRenderProperties)
