import bpy

from . import tree, sockets, nodes, categories


class TaichiBlendNodeSystem:
    def __init__(self, name, module):
        self.name = name
        self.prefix = 'taichi_blend_{}'.format(name)
        self.cap_prefix = 'TaichiBlend{}'.format(name.capitalize())
        self.window_icon = name.upper()
        self.window_label = 'Taichi Blend {}'.format(name.capitalize())
        self.module = module

        self.tree = None
        self.nodes = []
        self.sockets = []
        self.categories = []
        self.categories_def = {}

        self.socket_defs = module.socket_defs

    def register_nodes(self):
        self.module.register_nodes(self)

    def unregister(self):
        self.module.unregister_callback(self)
        for node in self.nodes:
            bpy.utils.unregister_class(node)


modules = [
    tree,
    sockets,
    nodes,
    categories,
]


def register():
    import os
    from ..utils import get_modules_list
    systems = get_modules_list(os.path.dirname(__file__), __name__)

    global node_systems
    node_systems = []
    for system_name, system in systems:
        if not hasattr(system, 'IsNoSys'):
            continue
        system = TaichiBlendNodeSystem(system_name, system)
        node_systems.append(system)

    for node_system in node_systems:
        for module in modules:
            module.register(node_system)


def unregister():
    for node_system in reversed(node_systems):
        for module in reversed(modules):
            module.unregister(node_system)
