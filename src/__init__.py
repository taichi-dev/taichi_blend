bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration for creating physic-based animations',
        'author': 'Taichi Developers',
        'version': (0, 0, 1),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}

__all__ = [
    'package_bundle',
    'node_system',
    'render_engine',
]

from . import *
modules = [globals()[x] for x in __all__]

def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
