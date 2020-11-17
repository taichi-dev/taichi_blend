import os

import bpy

from . import utils as nodes_utils
from .. import utils


def register(node_system):
    '''
    nodes_dir = os.path.dirname(__file__)
    modules = utils.get_modules_list(nodes_dir, __name__)
    for module_name, module in modules:
        if hasattr(module, 'Def'):
            nodes_utils.register_node(module_name, module.Def, node_system)
    '''

    import tina
    for name, cls in tina.ns_nodes.items():
        nodes_utils.register_node(name, cls, node_system)


def unregister(node_system):
    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
