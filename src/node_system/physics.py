IsNoSys = 1

from . import utils


DARK = 0.39, 0.39, 0.39
GRAY = 0.63, 0.63, 0.63
BLUE = 0.39, 0.39, 0.78
GREEN = 0.39, 0.78, 0.39
MAGENTA = 0.78, 0.16, 0.78
RED = 0.78, 0.39, 0.39
YELLOW = 0.78, 0.78, 0.16
CYAN = 0.16, 0.78, 0.78


socket_defs = {
    'field': DARK,
    'cached_field': GRAY,
    'vector_field': BLUE,
    'callable': GREEN,
    'matrix': MAGENTA,
    'task': RED,
    'meta': YELLOW,
    'any': CYAN,
}


def register_nodes(node_system):
    from . import blendina

    blendina.register()

    for name, cls in blendina.A.nodes.items():
        utils.register_node(name, cls, node_system)


def unregister_callback(node_system):
    from . import blendina
    blendina.unregister()
