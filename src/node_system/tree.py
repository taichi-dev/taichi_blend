import bpy


def make_node_tree_class(node_system):
    class TaichiBlendNodeTree(bpy.types.NodeTree):
        bl_idname = node_system.prefix + '_node_tree'
        bl_label = node_system.window_label
        bl_icon = node_system.window_icon

        @classmethod
        def poll(cls, context):
            return True

    return TaichiBlendNodeTree


def register(node_system):

    node_system.tree = make_node_tree_class(node_system)
    bpy.utils.register_class(node_system.tree)


def unregister(node_system):
    bpy.utils.unregister_class(node_system.tree)
