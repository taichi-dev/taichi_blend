import os, importlib


def get_modules_list(directory, packed):
    modules = []
    for file in os.listdir(path=directory):
        if not file.endswith('.py'):
            continue
        if not os.path.isfile(os.path.join(directory, file)):
            continue
        module_name = os.path.splitext(file)[0]
        module = importlib.import_module('.' + module_name, packed)
        modules.append((module_name, module))
    return modules
