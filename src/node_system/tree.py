import bpy


class TaichiBlendNodeTree(bpy.types.NodeTree):
    bl_idname = 'taichi_blend_node_tree'
    bl_label = 'Taichi Blend'
    bl_icon = 'PHYSICS'

    @classmethod
    def poll(cls, context):
        return True


def register(node_system):
    node_system.tree = TaichiBlendNodeTree
    bpy.utils.register_class(node_system.tree)


def unregister(node_system):
    bpy.utils.unregister_class(node_system.tree)
