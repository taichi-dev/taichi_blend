import os, importlib

import nodeitems_utils

from . import base
from .. import utils


def register(node_system):
    for category_system_name, nodes_ids in node_system.categories_def.items():
        items = []
        for node_id in nodes_ids:
            items.append(nodeitems_utils.NodeItem(node_id))
        category_id = 'taichi_blend_{}_node_category'.format(category_system_name)
        category = base.TaichiBlendNodeCategory(
            category_id,
            category_system_name.capitalize(),
            items=items
        )
        node_system.categories.append(category)
    nodeitems_utils.register_node_categories(node_system.tree.bl_idname, node_system.categories)


def unregister(node_system):
    nodeitems_utils.unregister_node_categories(node_system.tree.bl_idname)
