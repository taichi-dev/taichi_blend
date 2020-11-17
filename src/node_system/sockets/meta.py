import bpy


class TaichiBlendMetaSocket(bpy.types.NodeSocket):
    bl_idname = 'taichi_blend_meta_socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.4, 0.5, 0.6, 1.0)


def register():
    bpy.utils.register_class(TaichiBlendMetaSocket)


def unregister():
    bpy.utils.unregister_class(TaichiBlendMetaSocket)
