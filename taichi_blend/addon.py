'''Blender addon intergration'''

import bpy
import numpy as np
from .numio import from_numpy, to_numpy
from .anim import update_frame_callback, clear_animations

bl_info = {
        'name': 'Taichi Blend',
        'description': 'Taichi Blender intergration for creating physic-based animations',
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
    if update_frame_callback not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(update_frame_callback)


def unregister():
    if update_frame_callback in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(update_frame_callback)
