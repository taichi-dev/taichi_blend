import bpy, nodeitems_utils


def make_base_category(node_system):
    class Def(nodeitems_utils.NodeCategory):
        @classmethod
        def poll(cls, context):
            return context.space_data.tree_type == node_system.prefix + '_node_tree'

    return Def
