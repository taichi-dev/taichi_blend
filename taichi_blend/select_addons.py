import bpy


addon_names = ['meltblend', 'realtimetina', 'ptina']
registered_addons = {}


def addons_get(name):
    def wrapped(self):
        return name in registered_addons

    return wrapped


def addons_set(name):
    def wrapped(self, value):
        if value:
            if name not in registered_addons:
                print('Taichi-Blend: register addon', name)
                module = __import__(name)
                module.register()
                registered_addons[name] = module
        else:
            if name in registered_addons:
                print('Taichi-Blend: unregister addon', name)
                module = registered_addons[name]
                del registered_addons[name]
                try:
                    module.unregister()
                except Exception:
                    import traceback
                    print(traceback.format_exc())

    return wrapped


class TaichiAddonsProperties(bpy.types.PropertyGroup):
    @classmethod
    def initialize(cls):
        cls.__annotations__ = {}
        for name in addon_names:
            prop = bpy.props.BoolProperty(name=name,
                    get=addons_get(name), set=addons_set(name))
            cls.__annotations__[name] = prop

TaichiAddonsProperties.initialize()


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

        for name in addon_names:
            layout.prop(addons, name)


classes = [
        TaichiAddonsProperties,
        TaichiAddonsPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.taichi_addons = bpy.props.PointerProperty(
            name='taichi_addons', type=TaichiAddonsProperties)

    addons_set('ptina')(None, True)


def unregister():
    del bpy.types.Scene.taichi_addons

    for name in addon_names:
        addons_set(name)(None, False)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
