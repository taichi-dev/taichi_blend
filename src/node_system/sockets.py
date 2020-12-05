import bpy


def make_socket(node_system, name, color):
    class Def(bpy.types.NodeSocket):
        bl_idname = node_system.prefix + f'_{name}_socket'

        def draw(self, context, layout, node, text):
            layout.label(text=text)

        def draw_color(self, context, node):
            return (*color, 1.0)

    return Def


def register(node_system):
    for name, color in node_system.socket_defs.items():
        socket = make_socket(node_system, name, color)
        node_system.sockets.append(socket)

    for socket in node_system.sockets:
        bpy.utils.register_class(socket)


def unregister(node_system):
    for socket in node_system.sockets:
        bpy.utils.unregister_class(socket)
