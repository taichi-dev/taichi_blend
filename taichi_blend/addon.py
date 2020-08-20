'''Blender addon intergration'''

import bpy
import numpy as np
from .numio import from_numpy, to_numpy
from .anim import anim_update_frame

'''
bl_info = {
        'name': 'Taichi',
        'description': 'Productive & portable programming language for writting high-performance physics engines & renders',
        'author': 'Taichi Developers',
        'version': (0, 0, 0),
        'blender': (2, 82, 0),
        'location': 'Scripting module',
        'warning': 'Work in progress',
        'support': 'COMMUNITY',
        'wiki_url': 'https://taichi.readthedocs.io/en/stable',
        'tracker_url': 'https://github.com/taichi-dev/taichi/issues',
        'category': 'Physics',
}


def register():
    if anim_update_frame in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(anim_update_frame)
    bpy.app.handlers.frame_change_pre.append(anim_update_frame)


def unregister():
    if anim_update_frame in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(anim_update_frame)
'''


if anim_update_frame not in bpy.app.handlers.frame_change_pre:
    bpy.app.handlers.frame_change_pre.append(anim_update_frame)
