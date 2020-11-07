import sys
import imp
import os


bl_info = {
        'name': 'Taichi Blend (dev mode)',
        'description': 'Taichi Blender intergration for creating physic-based animations',
        'author': 'Taichi Developers',
        'version': (0, 0, 0),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'warning': 'Development mode',
        'category': 'Physics',
}


#repo_path = 'C:/Users/Administrator/taichi_blend'
repo_path = '/home/bate/Develop/blender_taichi'
src_path = os.path.join(repo_path, 'src/__init__.py')
build_path = os.path.join(repo_path, 'build/Taichi-Blend/bundle-packages')
assert os.path.exists(src_path), f'{src_path} does not exist!'
assert os.path.exists(build_path), f'{build_path} does not exist!'


taichi_blend = None

def register():
    print('Taichi-Blend repo at', repo_path)
    if build_path not in sys.path:
        sys.path.insert(0, build_path)

    global taichi_blend
    taichi_blend = imp.load_source('Taichi-Blend', src_path)
    taichi_blend.register()


def unregister():
    if build_path in sys.path:
        sys.path.remove(build_path)

    global taichi_blend
    taichi_blend.unregister()
    taichi_blend = None
