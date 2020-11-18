import bpy

from .nodes import utils




class TaichiApplyOperator(bpy.types.Operator):
    '''Apply Taichi tree'''

    bl_idname = "scene.taichi_apply"
    bl_label = "Apply"

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.taichi_node_group in bpy.data.node_groups

    def execute(self, context):
        import taichi as ti
        backend = bpy.context.scene.taichi_use_backend.lower()
        ti.init(arch=getattr(ti, backend))

        name = bpy.context.scene.taichi_node_group
        table = utils.get_node_table(bpy.data.node_groups[name])

        output = table['Output Task']
        output.run()

        return {'FINISHED'}


class TaichiPanel(bpy.types.Panel):
    '''Taichi options'''

    bl_label = 'Taichi'
    bl_idname = 'SCENE_PT_taichi'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop_search(scene, 'taichi_node_group',
                bpy.data, 'node_groups', text='Tree')
        layout.prop(scene, 'taichi_use_backend')
        layout.operator('scene.taichi_apply')
        layout.operator('render.render')


def register(node_system):
    bpy.types.Scene.taichi_node_group = bpy.props.StringProperty()
    bpy.types.Scene.taichi_use_backend = bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'Cuda', 'OpenCL', 'OpenGL', 'Metal', 'CC',
            ]])

    bpy.utils.register_class(TaichiApplyOperator)
    bpy.utils.register_class(TaichiPanel)


def unregister(node_system):
    bpy.utils.unregister_class(TaichiPanel)
    bpy.utils.unregister_class(TaichiApplyOperator)

    del bpy.types.Scene.taichi_node_group
    del bpy.types.Scene.taichi_use_backend
