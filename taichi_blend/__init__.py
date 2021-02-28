bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration',
        'author': 'archibate <1931127624@qq.com>',
        'version': (0, 0, 7),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}


from . import package_bundle, select_addons, taichi_worker

modules = [package_bundle, select_addons, taichi_worker]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
