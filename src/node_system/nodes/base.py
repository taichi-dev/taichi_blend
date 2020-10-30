import bpy


class TaichiBlendBaseNode(bpy.types.Node):
    @classmethod
    def poll(cls, node_tree):
        return node_tree.bl_idname == 'taichi_blend_node_tree'
