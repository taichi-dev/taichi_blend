import bpy

from . import tree, sockets, nodes, categories


class TaichiBlendNodeSystem:
    def __init__(self):
        self.tree = None
        self.nodes = []
        self.sockets = []
        self.categories = []
        self.categories_def = {}


node_system = TaichiBlendNodeSystem()
modules = [
    tree,
    sockets,
    nodes,
    categories,
]


def register():
    for module in modules:
        module.register(node_system)


def unregister():
    for module in reversed(modules):
        module.unregister(node_system)
