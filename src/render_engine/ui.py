import bpy


class TaichiRenderPanel(bpy.types.Panel):
    bl_label = 'Taichi Render'
    bl_idname = 'RENDER_PT_taichi'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop_search(scene, 'taichi_render_text', bpy.data, 'texts', text='Script')
        layout.operator('render.render')


def register():
    bpy.types.Scene.taichi_render_text = bpy.props.StringProperty()
    bpy.utils.register_class(TaichiRenderPanel)


def unregister():
    bpy.utils.unregister_class(TaichiRenderPanel)
    del bpy.types.Scene.taichi_render_text
