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
        worker = scene.taichi_worker

        layout.prop(worker, 'backend')
        if worker.backend in {'CUDA', 'GPU'}:
            layout.prop(worker, 'memory_fraction')
            layout.prop(worker, 'memory_GB')


class TaichiWorkerProperties(bpy.types.PropertyGroup):
    backend: bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'CUDA', 'OpenGL', 'Metal', 'CC',
            ]], default='CUDA')
    memory_fraction: bpy.props.IntProperty(name='Memory Fraction',
            min=0, max=100, default=0, subtype='PERCENTAGE')
    memory_GB: bpy.props.FloatProperty(name='Memory GB',
            min=0, default=1.5, subtype='UNSIGNED', precision=1)


def get_arguments(scene=None):
    if scene is None:
        scene = bpy.context.scene
    options = scene.taichi_worker

    kwargs = {}

    kwargs['arch'] = getattr(ti, options.backend.lower())
    if scene.memory_fraction > 0:
        kwargs['device_memory_fraction'] = options.memory_fraction / 100
    elif scene.memory_GB > 0:
        kwargs['device_memory_GB'] = options.memory_GB


classes = [
        TaichiWorkerProperties,
        TaichiWorkerPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.taichi_worker = bpy.props.PointerProperty(
            name='taichi_worker', type=TaichiWorkerProperties)


def unregister():
    del bpy.types.Scene.taichi_worker

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
