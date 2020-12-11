bl_info = {
        'name': 'Tina (dev mode)',
        'description': 'A soft-renderer based on Taichi programming language',
        'author': '彭于斌 <1931127624@qq.com>',
        'version': (0, 0, 0),
        'blender': (2, 81, 0),
        'location': 'Render -> Tina',
        'support': 'TESTING',
        'wiki_url': 'https://github.com/archibate/tina/wiki',
        'tracker_url': 'https://github.com/archibate/tina/issues',
        'warning': 'Development mode',
        'category': 'Render',
}


import sys
sys.path.insert(0, '/home/bate/Develop/seven')


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


registered = False


def register():
    print('Tina-Dev register...')
    import tina
    tina.register()

    global registered
    registered = True
    print('...register done')


def unregister():
    print('Tina-Dev unregister...')
    import tina
    tina.unregister()

    global registered
    registered = False
    print('...unregister done')


def reload():
    import tina
    if registered:
        unregister()
    reload_package(tina)
    register()

    import bpy
    bpy.context.scene.frame_current = bpy.context.scene.frame_current

__import__('bpy').a = reload
