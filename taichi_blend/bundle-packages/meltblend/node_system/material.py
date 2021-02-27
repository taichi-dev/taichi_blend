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
    'scalar': GRAY,
    'vector': BLUE,
    'color': YELLOW,
    'material': GREEN,
    'any': DARK,
}


def get_sockets_def(node_system):
    return sockets_def


def get_nodes_def(node_system):
    import tina.melty
    return tina.melty.A.nodes


def register_callback(node_system):
    import tina
    tina.register()


def unregister_callback(node_system):
    import tina
    tina.unregister()
