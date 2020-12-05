import os
import bpy

from . import base


def register(node_system):
    node_system.base_node = base.make_base_node(node_system)

    node_system.register_nodes()
