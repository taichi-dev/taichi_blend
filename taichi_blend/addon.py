'''Blender addon intergration'''

import bpy
import numpy as np
from .numio import from_numpy, to_numpy
from .anim import update_frame_callback, clear_animations


def register():
    if update_frame_callback not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(update_frame_callback)


def unregister():
    if update_frame_callback in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(update_frame_callback)
