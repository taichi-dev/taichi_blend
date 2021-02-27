bl_info = {
        'name': 'Tina',
        'description': 'A soft renderer based on Taichi programming language',
        'author': 'archibate <1931127624@qq.com>',
        'version': (0, 1, 0),
        'blender': (2, 90, 0),
        'location': 'Render -> Tina',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_three/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_three/issues',
        'category': 'Render',
}


def register():
    from . import blender
    return blender.register()


def unregister():
    from . import blender
    return blender.unregister()
