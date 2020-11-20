import os
import bpy

from . import utils


def register(node_system):
    from . import blendina
    blendina.register()

    for name, cls in blendina.A.nodes.items():
        utils.register_node(name, cls, node_system)


def unregister(node_system):
    from . import blendina
    blendina.unregister()

    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
