import sys
import os


bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration for creating physic-based animations',
        'author': 'Taichi Developers',
        'version': (0, 0, 0),
        'blender': (2, 82, 0),
        'location': 'Scripting module',
        'warning': 'Work in progress',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'category': 'Physics',
}


for p in sys.path:
    bundle_path = os.path.join(p, 'Taichi-Blend')
    if os.path.exists(bundle_path):
        break
else:
    raise Exception('Cannot find Taichi-Blend!')


def register():
    print('Found Taichi-Blend at', bundle_path)
    if bundle_path not in sys.path:
        sys.path.insert(0, bundle_path)

def unregister():
    if bundle_path in sys.path:
        sys.path.remove(bundle_path)
