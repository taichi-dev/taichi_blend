import bpy

from . import field, task, meta


modules = [
    field,
    task,
    meta,
]


def register(node_system):
    for module in modules:
        module.register()


def unregister(node_system):
    for module in reversed(modules):
        module.unregister()
