import os, importlib
import nodeitems_utils

from . import base


def register(node_system):
    node_system.base_category = base.make_base_category(node_system)

    for category_system_name, nodes_ids in node_system.categories_def.items():
        items = []
        for node_id in nodes_ids:
            items.append(nodeitems_utils.NodeItem(node_id))
        category_id = node_system.prefix + '_{}_node_category'.format(category_system_name)
        category = node_system.base_category(
            category_id,
            category_system_name.capitalize(),
            items=items
        )
        node_system.categories.append(category)
    nodeitems_utils.register_node_categories(node_system.tree.bl_idname, node_system.categories)


def unregister(node_system):
    nodeitems_utils.unregister_node_categories(node_system.tree.bl_idname)
