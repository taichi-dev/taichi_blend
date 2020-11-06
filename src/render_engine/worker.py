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


def get_render_script():
    text_name = bpy.context.scene.taichi_render_text
    text_string = bpy.data.texts[text_name].as_string()
    fd, path = tempfile.mkstemp(prefix='taichiblend-', suffix='.py')
    os.close(fd)
    with open(path, 'w') as f:
        f.write(text_string)
    text_dict = runpy.run_path(path, run_name=text_name)
    atexit.register(os.unlink, path)
    return text_dict


def taichi_worker(engine):
    hint = f'[taichi_worker:{threading.get_ident()}]'

    print(hint, 'started')
    while engine.running:
        try:
            cmd, *args = engine.queue.get(block=True, timeout=10)
        except queue.Empty:
            continue

        try:
            if cmd == 'UPDATE':
                text = get_render_script()

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

    def render(self, width, height, view):
        pixels = np.empty(width * height * 4, dtype=np.float32)
        render_args = pixels, width, height, view
        try:
            self.queue.put(['RENDER', *render_args], block=True, timeout=1)
        except queue.Full:
            print('Taichi worker queue full')
        self.queue.join()
        return pixels
