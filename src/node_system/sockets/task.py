import bpy


class TaichiBlendTaskSocket(bpy.types.NodeSocket):
    bl_idname = 'taichi_blend_task_socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.0, 0.8, 0.0, 1.0)


def register():
    bpy.utils.register_class(TaichiBlendTaskSocket)


def unregister():
    bpy.utils.unregister_class(TaichiBlendTaskSocket)
