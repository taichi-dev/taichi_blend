bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration',
        'author': 'Taichi Developers',
        'version': (0, 0, 4),
        'blender': (2, 81, 0),
        'location': 'Taichi Blend Window',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}

from . import package_bundle, node_system, user_iface

modules = [
    package_bundle,
    node_system,
    user_iface,
]

def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
