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
        'support': 'TESTING',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'warning': 'Development mode',
        'category': 'Physics',
}


#repo_path = 'C:/Users/Administrator/taichi_blend'
repo_path = '/home/bate/Develop/blender_taichi'
src_path = os.path.join(repo_path, 'src/__init__.py')
bundle_path = os.path.join(repo_path, 'src/bundle-packages')
assert os.path.exists(src_path), f'{src_path} does not exist!'
assert os.path.exists(bundle_path), f'{bundle_path} does not exist!'


taichi_blend = None

def register():
    print('Taichi-Blend repo at', repo_path)
    if bundle_path not in sys.path:
        sys.path.insert(0, bundle_path)

    global taichi_blend
    taichi_blend = imp.load_source('Taichi-Blend', src_path)
    taichi_blend.register()


def unregister():
    if build_path in sys.path:
        sys.path.remove(build_path)
    if bundle_path in sys.path:
        sys.path.remove(bundle_path)

    global taichi_blend
    taichi_blend.unregister()
    taichi_blend = None


def reload():
    import tina
    if taichi_blend is not None:
        unregister()
    reload_package(tina)
    register()

    import bpy
    bpy.context.scene.frame_current = bpy.context.scene.frame_current

__import__('bpy').a = reload

# https://stackoverflow.com/questions/28101895/reloading-packages-and-their-submodules-recursively-in-python
def reload_package(package):
    import os
    import types
    import importlib

    assert(hasattr(package, "__package__"))
    fn = package.__file__
    fn_dir = os.path.dirname(fn) + os.sep
    module_visit = {fn}
    del fn

    def reload_recursive_ex(module):
        importlib.reload(module)

        for module_child in vars(module).values():
            if isinstance(module_child, types.ModuleType):
                fn_child = getattr(module_child, "__file__", None)
                if (fn_child is not None) and fn_child.startswith(fn_dir):
                    if fn_child not in module_visit:
                        # print("reloading:", fn_child, "from", module)
                        module_visit.add(fn_child)
                        reload_recursive_ex(module_child)

    reload_recursive_ex(package)
