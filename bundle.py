import sys
import os


bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration for creating physic-based animations',
        'author': 'Taichi Developers',
        'version': (0, 0, 1),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'warning': 'Work in progress',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}


bundle_path = os.path.abspath(os.path.dirname(__file__))
assert os.path.exists(bundle_path), f'{bundle_path} does not exist!'


def register():
    print('Taichi-Blend bundle at', bundle_path)
    if bundle_path not in sys.path:
        sys.path.insert(0, bundle_path)

def unregister():
    if bundle_path in sys.path:
        sys.path.remove(bundle_path)
