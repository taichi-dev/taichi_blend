from . import engine, panel

modules = [
    engine,
    panel,
]

def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
