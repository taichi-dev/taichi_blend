import bpy


class AddonReloadOperator(bpy.types.Operator):
    '''Reload Taichi-blend addon'''

    bl_idname = "scene.taichi_blend_reload_addon"
    bl_label = "Reload Taichi-blend"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        module = __import__('Taichi-Blend')
        module.unregister()
        module.register()
        return {'FINISHED'}



class DeveloperUtilsPanel(bpy.types.Panel):
    '''Taichi-blend developer utilities'''

    bl_label = 'Taichi-blend dev utils'
    bl_idname = 'RENDER_PT_taichi_blend_dev_utils'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator('scene.taichi_blend_reload_addon')


def register():
    bpy.utils.register_class(AddonReloadOperator)
    bpy.utils.register_class(DeveloperUtilsPanel)


def unregister():
    bpy.utils.unregister_class(DeveloperUtilsPanel)
    bpy.utils.unregister_class(AddonReloadOperator)
