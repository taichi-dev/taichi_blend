import sys
import imp
import os


bl_info = {
        'name': 'Taichi Blend (dev mode)',
        'description': 'Taichi Blender intergration',
        'author': 'archibate <1931127624@qq.com>',
        'version': (0, 0, 0),
        'blender': (2, 81, 0),
        'location': 'Scripting module',
        'support': 'TESTING',
        'wiki_url': 'https://github.com/taichi-dev/taichi_blend/wiki',
        'tracker_url': 'https://github.com/taichi-dev/taichi_blend/issues',
        'warning': 'Development mode',
        'category': 'Physics',
}


repo_path = '/home/bate/Develop/blender_taichi'

sys.path.insert(0, repo_path)
sys.path.insert(0, os.path.join(repo_path, 'external/ptina'))


registered = False


def register():
    print('Taichi-Blend-Dev register...')
    import taichi_blend
    taichi_blend.register()

    global registered
    registered = True
    print('...register done')


def unregister():
    print('Taichi-Blend-Dev unregister...')
    import taichi_blend
    taichi_blend.unregister()

    global registered
    registered = False
    print('...unregister done')


def reload_addon():
    if registered:
        import taichi_blend
        taichi_blend.unregister()
        del taichi_blend
    mods_to_del = []
    for k, v in sys.modules.items():
        if hasattr(v, '__file__') and v.__file__ is not None:
            if v.__file__.startswith(repo_path):
                print('reloading', k)
                mods_to_del.append(k)
    for k in mods_to_del:
        sys.modules.pop(k)
    import taichi_blend
    taichi_blend.register()


@eval('lambda x: x()')
def _():
    class Reload:
        def __repr__(self):
            import os
            import bpy
            os.system('clear')
            reload_addon()
            bpy.context.scene.frame_current = bpy.context.scene.frame_current
            return 'reloaded'

    __import__('bpy').a = Reload()
