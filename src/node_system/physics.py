IsNoSys = 1


DARK = 0.39, 0.39, 0.39
GRAY = 0.63, 0.63, 0.63
BLUE = 0.39, 0.39, 0.78
GREEN = 0.39, 0.78, 0.39
MAGENTA = 0.78, 0.16, 0.78
RED = 0.78, 0.39, 0.39
YELLOW = 0.78, 0.78, 0.16
CYAN = 0.16, 0.78, 0.78


sockets_def = {
    'field': DARK,
    'cached_field': GRAY,
    'vector_field': BLUE,
    'callable': GREEN,
    'matrix': MAGENTA,
    'task': RED,
    'meta': YELLOW,
    'any': CYAN,
}


def get_sockets_def(node_system):
    return sockets_def


def get_nodes_def(node_system):
    import melt.blender
    return melt.A.nodes


def register_callback(node_system):
    import melt.blender
    melt.blender.register()


def unregister_callback(node_system):
    import melt.blender
    melt.blender.unregister()
