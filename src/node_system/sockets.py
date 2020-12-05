import bpy


def make_socket(name, color):
    class Def(bpy.types.NodeSocket):
        bl_idname = f'taichi_blend_{name}_socket'

        def draw(self, context, layout, node, text):
            layout.label(text=text)

        def draw_color(self, context, node):
            return (*color, 1.0)

    return Def


DARK = 0.39, 0.39, 0.39
GRAY = 0.63, 0.63, 0.63
BLUE = 0.39, 0.39, 0.78
GREEN = 0.39, 0.78, 0.39
MAGENTA = 0.78, 0.16, 0.78
RED = 0.78, 0.39, 0.39
YELLOW = 0.78, 0.78, 0.16
CYAN = 0.16, 0.78, 0.78

sockets = {
    'field': DARK,
    'cached_field': GRAY,
    'vector_field': BLUE,
    'callable': GREEN,
    'matrix': MAGENTA,
    'task': RED,
    'meta': YELLOW,
    'any': CYAN,
}
sockets = [make_socket(name, color) for name, color in sockets.items()]


def register(node_system):
    for socket in sockets:
        bpy.utils.register_class(socket)


def unregister(node_system):
    for socket in sockets:
        bpy.utils.unregister_class(socket)
