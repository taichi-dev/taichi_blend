'''
load a worker module to operate in a separate thread, see tina/worker.py
'''

import functools
import threading
import traceback
import queue
import time


class DaemonThread(threading.Thread):
    def __init__(self, func, *args):
        super().__init__(daemon=True)
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)


class DaemonWorker:
    def __init__(self):
        self.queue = queue.Queue()
        self.daemon = DaemonThread(self.daemon_main)
        self.daemon.start()

    def daemon_main(self):
        while True:
            func = self.queue.get()
            try:
                ret = func()
            except BaseException:
                print(traceback.format_exc())
                ret = None
            func.retval = ret
            self.queue.task_done()

    def launch(self, func):
        self.queue.put(func)
        self.queue.join()
        return func.retval


class DaemonModule:
    def __init__(self, getmodule):
        self._worker = DaemonWorker()

        @self._worker.launch
        def _():
            self._module = getmodule()

    def _wrap(self, func):
        if not callable(func):
            return func

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            @self._worker.launch
            def retval():
                return func(*args, **kwargs)

            return self._wrap(retval)

        return wrapped

    def __getattr__(self, name):
        func = getattr(self._module, name)
        return self._wrap(func)


class OnDemandProxy:
    def __init__(self, getmodule):
        self._getmodule = getmodule
        self._module = None
        self._lock = threading.Lock()

    def _try_load(self):
        if self._module is None:
            with self._lock:
                if self._module is None:
                    self._module = self._getmodule()

    def __getattr__(self, name):
        self._try_load()
        return getattr(self._module, name)


if __name__ == '__main__':
    @DaemonModule
    def ti():
        import taichi
        return taichi

    ti.init(ti.opengl)

    @ti.kernel
    def func():
        print('hello')

    func()
