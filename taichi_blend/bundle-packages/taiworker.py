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
        layout.prop(worker, 'memory_fraction')
        layout.prop(worker, 'memory_GB')
        layout.prop(worker, 'unified_memory')
        layout.prop(worker, 'block_local')
        layout.prop(worker, 'cpu_threads')
        layout.prop(worker, 'int_precision')
        layout.prop(worker, 'float_precision')


class TaichiWorkerProperties(bpy.types.PropertyGroup):
    backend: bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'CUDA', 'OpenGL', 'Metal', 'CC',
            ]], default='CUDA')
    cpu_threads: bpy.props.IntProperty(name='CPU Threads', min=0, default=0)
    memory_fraction: bpy.props.IntProperty(name='CUDA Memory Fraction',
            min=0, max=100, default=0, subtype='PERCENTAGE')
    memory_GB: bpy.props.FloatProperty(name='CUDA Memory GB',
            min=0, default=1.5, subtype='UNSIGNED', precision=2)
    unified_memory: bpy.props.BoolProperty(name='CUDA Unified Memory',
            default=True)
    block_local: bpy.props.BoolProperty(name='CUDA Block local',
            default=True)
    backend: bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'CUDA', 'OpenGL', 'Metal', 'CC',
            ]], default='GPU')
    int_precision: bpy.props.EnumProperty(name='Integer Precision',
            items=[(item.upper(), item, '') for item in [
                'Auto', 'Int32', 'Int64']], default='AUTO')
    float_precision: bpy.props.EnumProperty(name='Float Precision',
            items=[(item.upper(), item, '') for item in [
                'Auto', 'Float32', 'Float64']], default='AUTO')


def get_initializer(scene=None):
    if scene is None:
        scene = bpy.context.scene
    options = scene.taichi_worker

    kwargs = {}
    exkwargs = {}

    exkwargs['arch'] = options.backend.lower()
    if options.cpu_threads > 0:
        kwargs['cpu_max_num_threads'] = options.cpu_threads
    if options.memory_fraction > 0:
        kwargs['device_memory_fraction'] = options.memory_fraction / 100
    elif options.memory_GB > 0:
        kwargs['device_memory_GB'] = options.memory_GB
    if not options.unified_memory:
        kwargs['use_unified_memory'] = False
    if not options.block_local:
        kwargs['make_block_local'] = False
    if options.int_precision != 'AUTO':
        exkwargs['default_ip'] = {
                'INT32': 'i32', 'INT64': 'i64'}[options.int_precision]
    if options.float_precision != 'AUTO':
        exkwargs['default_fp'] = {
                'FLOAT32': 'f32', 'FLOAT64': 'f64'}[options.float_precision]

    def initializer(*extra_args, **extra_kwargs):
        import taichi as ti
        final_kwargs = {}
        for k, v in kwargs.items():
            final_kwargs[k] = v
        for k, v in exkwargs.items():
            final_kwargs[k] = getattr(ti, v)
        for k, v in extra_kwargs.items():
            final_kwargs[k] = v
        ti.init(*extra_args, **final_kwargs)

    return initializer


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
