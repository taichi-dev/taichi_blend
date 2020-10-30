import bpy, nodeitems_utils


class TaichiBlendNodeCategory(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'taichi_blend_node_tree'
