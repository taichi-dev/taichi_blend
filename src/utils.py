import os, sys
import importlib
import threading
import tempfile
import atexit


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


def run_source(source, run_name=None):
    fd, path = tempfile.mkstemp(prefix='taichiblend-', suffix='.py')
    os.close(fd)
    with open(path, 'w') as f:
        f.write(source)
    module = runpy.run_path(path, run_name=run_name)
    atexit.register(os.unlink, path)
    return module


class singleton:
    def __init__(self, cls):
        self._class = cls
        self._instance_lock = threading.Lock()
        self._instance = None

    def __call__(self, *args, **kwargs):
        with self._instance_lock:
            if self._instance is None:
                self._instance = self._class(*args, **kwargs)
            return self._instance

    def __getattr__(self, attr):
        return getattr(self._class, attr)

    def _delete_instance(self):
        with self._instance_lock:
            self._instance = None
