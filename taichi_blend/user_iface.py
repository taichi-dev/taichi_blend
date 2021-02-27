import bpy


class TaichiWorkerPanel(bpy.types.Panel):
    '''Taichi worker options'''

    bl_label = 'Taichi Worker'
    bl_idname = 'SCENE_PT_taichi_worker'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, 'taichi_backend')


import tina
registered_addons = [tina]


def on_addon_update(name):
    def callback(self, context=None):
        enable = getattr(self, name)
        module = __import__(name)
        if enable:
            module.register()
            registered_addons.append(module)
        else:
            try:
                module.unregister()
            except Exception:
                import traceback
                print(traceback.format_exc())
            registered_addons.remove(module)

    return callback


class TaichiAddonsProperties(bpy.types.PropertyGroup):
    meltblend: bpy.props.BoolProperty(name='Taichi Blend Physics', default=False, update=on_addon_update('meltblend'))
    realtimetina: bpy.props.BoolProperty(name='Real-time Tina', default=False, update=on_addon_update('realtimetina'))
    tina: bpy.props.BoolProperty(name='Tina Path Tracer', default=True, update=on_addon_update('tina'))


class TaichiAddonsPanel(bpy.types.Panel):
    '''Taichi addons options'''

    bl_label = 'Taichi Addons'
    bl_idname = 'SCENE_PT_taichi_addons'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        addons = scene.taichi_addons

        layout.prop(addons, 'tina')
        layout.prop(addons, 'meltblend')
        layout.prop(addons, 'realtimetina')


classes = [
        TaichiAddonsProperties,
        TaichiWorkerPanel,
        TaichiAddonsPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.taichi_addons = bpy.props.PointerProperty(
            name='taichi_addons', type=TaichiAddonsProperties)
    bpy.types.Scene.taichi_backend = bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'CUDA', 'OpenGL', 'Metal', 'CC',
            ]], default='CUDA')

    for mod in registered_addons:
        mod.register()


def unregister():
    del bpy.types.Scene.taichi_backend
    del bpy.types.Scene.taichi_addons

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    for mod in reversed(registered_addons):
        mod.unregister()
