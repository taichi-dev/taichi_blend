import os
import bpy

from . import utils


def register(node_system):
    import tina
    from . import extra  # register some extra nodes to tina.A

    for name, cls in tina.A.nodes.items():
        utils.register_node(name, cls, node_system)


def unregister(node_system):
    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
