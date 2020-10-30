import bpy


class TaichiBlendFieldSocket(bpy.types.NodeSocket):
    bl_idname = 'taichi_blend_field_socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.25, 0.25, 0.25, 1.0)


def register():
    bpy.utils.register_class(TaichiBlendFieldSocket)


def unregister():
    bpy.utils.unregister_class(TaichiBlendFieldSocket)
