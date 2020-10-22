import sys
import os


bl_info = {
        'name': 'Taichi Blend (dev mode)',
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


repo_path = 'C:/Users/Administrator/taichi_blend'
src_path = os.path.join(repo_path, 'src/bundle-packages')
build_path = os.path.join(repo_path, 'build/Taichi-Blend/bundle-packages')
assert os.path.exists(src_path), f'{src_path} does not exist!'
assert os.path.exists(build_path), f'{build_path} does not exist!'


def register():
    print('Taichi-Blend repo at', repo_path)
    if build_path not in sys.path:
        sys.path.insert(0, build_path)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def unregister():
    if build_path in sys.path:
        sys.path.remove(build_path)
    if src_path in sys.path:
        sys.path.remove(src_path)