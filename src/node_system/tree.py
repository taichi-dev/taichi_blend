import bpy


class TaichiBlendNodeTree(bpy.types.NodeTree):
    bl_idname = 'taichi_blend_node_tree'
    bl_label = 'Taichi Blend'
    bl_icon = 'PHYSICS'

    @classmethod
    def poll(cls, context):
        return True


def register(node_system):
    '''
    global pcoll
    import os, bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    logo_path = os.path.join(os.path.dirname(__file__), 'taichi_logo.png')
    pcoll.load('taichi_logo', logo_path, 'IMAGE')
    TaichiBlendNodeTree.bl_icon = pcoll['taichi_logo'].icon_id
    '''

    node_system.tree = TaichiBlendNodeTree
    bpy.utils.register_class(node_system.tree)


def unregister(node_system):
    bpy.utils.unregister_class(node_system.tree)
