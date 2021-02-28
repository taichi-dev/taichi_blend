bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration',
        'author': 'Taichi Developers',
        'version': (0, 0, 7),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}


import sys
import os


bundle_path = os.path.join(os.path.dirname(__file__), 'bundle-packages')


def register():
    print('Taichi-Blend package bundle at', bundle_path)
    assert os.path.exists(bundle_path), f'{bundle_path} does not exist!'
    if bundle_path not in sys.path:
        sys.path.insert(0, bundle_path)


def unregister():
    if bundle_path in sys.path:
        sys.path.remove(bundle_path)
