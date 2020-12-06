bl_info = {
        'name': 'Tina',
        'description': 'A soft-renderer based on Taichi programming language',
        'author': '彭于斌 <1931127624@qq.com>',
        'version': (0, 0, 0),
        'blender': (2, 81, 0),
        'location': 'Render -> Tina Options',
        'support': 'COMMUNITY',
        'wiki_url': 'https://github.com/archibate/tina/wiki',
        'tracker_url': 'https://github.com/archibate/tina/issues',
        'category': 'Render',
}

__version__ = bl_info['version']
__author__ = bl_info['author']

print('[Tina] version', '.'.join(map(str, __version__)))


def register():
    from . import blend
    blend.register()


def unregister():
    from . import blend
    blend.unregister()


from .hacker import *
from .common import *
from .advans import *
from .core import *
from .util import *
