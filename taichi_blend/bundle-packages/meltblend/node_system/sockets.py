import bpy


def make_socket(node_system, name, socket_def):
    color = socket_def  # TODO: support inline const properties

    class Def(bpy.types.NodeSocket):
        bl_idname = node_system.prefix + f'_{name}_socket'

        def draw(self, context, layout, node, text):
            layout.label(text=text)

        def draw_color(self, context, node):
            return (*color, 1.0)

    return Def


def register(node_system):
    for name, socket_def in node_system.get_sockets_def().items():
        socket = make_socket(node_system, name, socket_def)
        node_system.sockets.append(socket)

    for socket in node_system.sockets:
        bpy.utils.register_class(socket)


def unregister(node_system):
    for socket in node_system.sockets:
        bpy.utils.unregister_class(socket)
