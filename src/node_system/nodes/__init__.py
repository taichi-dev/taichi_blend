import os
import bpy

from . import utils


def register(node_system):
    '''
    from ..utils import get_modules_list
    nodes_dir = os.path.dirname(__file__)
    modules = get_modules_list(nodes_dir, __name__)
    for module_name, module in modules:
        if hasattr(module, 'Def'):
            utils.register_node(module_name, module.Def, node_system)
    '''
    import tina

    for name, cls in tina.ns_nodes.items():
        utils.register_node(name, cls, node_system)


def unregister(node_system):
    for node in node_system.nodes:
        bpy.utils.unregister_class(node)
