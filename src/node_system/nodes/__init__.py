import os
import bpy

from . import utils


def register(node_system):
    from . import blendina
    blendina.register()

    def register_node(name, cls):
        utils.register_node(name, cls, node_system)

    for name, cls in blendina.A.nodes.items():
        register_node(name, cls)

    blendina.A.register_callback = register_node


def unregister(node_system):
    from . import blendina
    blendina.unregister()

    blendina.A.register_callback = lambda name, cls: None

    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
