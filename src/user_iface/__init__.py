from . import engine, render, panel

modules = [
    engine,
    render,
    panel,
]

def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()

