import bpy


def make_socket(name, color):
    class Def(bpy.types.NodeSocket):
        bl_idname = f'taichi_blend_{name}_socket'

        def draw(self, context, layout, node, text):
            layout.label(text=text)

        def draw_color(self, context, node):
            return (*color, 1.0)

    return Def


sockets = {
    'field': (0.63, 0.63, 0.63),
    'vector_field': (0.39, 0.39, 0.78),
    'meta_field': (0.39, 0.78, 0.39),
    'task': (0.78, 0.39, 0.39),
    'meta': (0.78, 0.78, 0.16),
}
sockets = [make_socket(name, color) for name, color in sockets.items()]


def register(node_system):
    for socket in sockets:
        bpy.utils.register_class(socket)


def unregister(node_system):
    for socket in sockets:
        bpy.utils.unregister_class(socket)
