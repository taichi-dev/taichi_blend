import bpy

from . import field, value, sampler


modules = [
    field,
    value,
    sampler
]


def register(node_system):
    for module in modules:
        module.register()


def unregister(node_system):
    for module in modules.reverse():
        module.unregister()
