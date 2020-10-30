import bpy


class TaichiBlendValueSocket(bpy.types.NodeSocket):
    bl_idname = 'taichi_blend_value_socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.5, 0.5, 0.5, 1.0)


def register():
    bpy.utils.register_class(TaichiBlendValueSocket)


def unregister():
    bpy.utils.unregister_class(TaichiBlendValueSocket)
