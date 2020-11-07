import bpy


class TaichiRenderUpdateOperator(bpy.types.Operator):
    '''Update Taichi rendering script'''

    bl_idname = "scene.taichi_render_update"
    bl_label = "Update"

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.taichi_render_text in bpy.data.texts

    def execute(self, context):
        text = bpy.context.scene.taichi_render_text
        source = bpy.data.texts[text].as_string()

        from .worker import TaichiWorker
        worker = TaichiWorker()
        try:
            worker.queue.put(['UPDATE', source], block=True, timeout=10)
        except queue.Full:
            return {'CANCELED'}

        return {'FINISHED'}


class TaichiRenderPanel(bpy.types.Panel):
    '''Taichi renderer options'''

    bl_label = 'Taichi'
    bl_idname = 'RENDER_PT_taichi'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop_search(scene, 'taichi_render_text', bpy.data, 'texts', text='Script')
        layout.operator('scene.taichi_render_update')
        layout.operator('render.render')


def register():
    bpy.types.Scene.taichi_render_text = bpy.props.StringProperty()
    bpy.utils.register_class(TaichiRenderUpdateOperator)
    bpy.utils.register_class(TaichiRenderPanel)


def unregister():
    bpy.utils.unregister_class(TaichiRenderPanel)
    bpy.utils.unregister_class(TaichiRenderUpdateOperator)
    del bpy.types.Scene.taichi_render_text
