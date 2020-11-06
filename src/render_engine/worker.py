import bpy
import bgl
import numpy as np
import threading
import traceback
import tempfile
import atexit
import queue
import runpy
import sys
import os


def run_source(source, run_name=None):
    fd, path = tempfile.mkstemp(prefix='taichiblend-', suffix='.py')
    os.close(fd)
    with open(path, 'w') as f:
        f.write(source)
    module = runpy.run_path(path, run_name=run_name)
    atexit.register(os.unlink, path)
    return module


def taichi_worker(engine):
    hint = f'[taichi_worker:{threading.get_ident()}]'

    print(hint, 'started')
    text = {'render': lambda *x: None}

    while engine.running:
        try:
            cmd, *args = engine.queue.get(block=True, timeout=10)
        except queue.Empty:
            continue

        try:
            if cmd == 'UPDATE':
                text = run_source(*args, run_name='render')

            elif cmd == 'RENDER':
                text['render'](*args)

        except Exception:
            print(hint, 'exception while running task:')
            print(traceback.format_exc())

        engine.queue.task_done()

    print(hint, 'stopped')


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


@singleton
class TaichiWorker:
    def __init__(self):
        self.running = True
        self.queue = queue.Queue(maxsize=4)
        self.worker = threading.Thread(target=taichi_worker, args=[self])
        self.worker.start()

    def stop(self):
        self.running = False
        self.queue.put(['STOP'], block=False)
        self.worker.join(timeout=3)

    def render(self, width, height, *args):
        pixels = np.empty(width * height * 4, dtype=np.float32)
        args = [pixels, width, height, *args]
        try:
            self.queue.put(['RENDER', *args], block=True, timeout=1)
        except queue.Full:
            print('Taichi worker queue full')
        self.queue.join()
        return pixels
