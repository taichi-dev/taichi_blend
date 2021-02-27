import os
import bpy

from . import base
from .. import utils


def register(node_system):
    node_system.base_node = base.make_base_node(node_system)

    for name, cls in node_system.get_nodes_def().items():
        utils.register_node(name, cls, node_system)


def unregister(node_system):
    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
