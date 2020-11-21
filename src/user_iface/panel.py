import bpy

from . import engine


class TaichiBlendApplyOperator(bpy.types.Operator):
    '''Apply Taichi Blend program'''

    bl_idname = "scene.taichi_apply"
    bl_label = "Apply"

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.taichi_node_group in bpy.data.node_groups

    def execute(self, context):
        engine.apply_main(self)
        return {'FINISHED'}


class TaichiBlendPanel(bpy.types.Panel):
    '''Taichi Blend program options'''

    bl_label = 'Taichi Blend'
    bl_idname = 'SCENE_PT_taichi_blend'
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


def register():
    bpy.types.Scene.taichi_node_group = bpy.props.StringProperty()
    bpy.types.Scene.taichi_use_backend = bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'CUDA', 'OpenCL', 'OpenGL', 'Metal', 'CC',
            ]])

    bpy.utils.register_class(TaichiBlendApplyOperator)
    bpy.utils.register_class(TaichiBlendPanel)


def unregister():
    bpy.utils.unregister_class(TaichiBlendPanel)
    bpy.utils.unregister_class(TaichiBlendApplyOperator)

    del bpy.types.Scene.taichi_node_group
    del bpy.types.Scene.taichi_use_backend
