import bpy


def make_base_node(node_system):
    class Def(bpy.types.Node):
        @classmethod
        def poll(cls, node_tree):
            return node_tree.bl_idname == node_system.prefix + '_node_tree'

    return Def
