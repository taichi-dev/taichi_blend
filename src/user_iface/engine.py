import bpy
import queue
import threading
import traceback
import numpy as np
import time

from ..node_system.nodes import utils


class TaichiWorker:
    def __init__(self):
        self.q = queue.Queue(maxsize=4)
        self.running = True

        self.t = threading.Thread(target=self.main)
        self.t.daemon = True
        self.t.start()

        self.table = None

    def stop(self):
        print('Stopping worker')
        if self.running:
            self.running = False
            self.q.put(lambda self: None, block=False)

    def main(self):
        print('Worker started')
        while self.running:
            try:
                func = self.q.get(block=True, timeout=1)
            except queue.Empty:
                continue

            try:
                func(self)
            except Exception:
                print('Exception while running task:')
                print(traceback.format_exc())

            self.q.task_done()

    def launch(self, func):
        self.q.put(func, block=True, timeout=None)

    def wait_done(self):
        self.q.join()


def taichi_init():
    import taichi as ti
    backend = bpy.context.scene.taichi_use_backend.lower()
    ti.init(arch=getattr(ti, backend))

    name = bpy.context.scene.taichi_node_group
    table = utils.get_node_table(bpy.data.node_groups[name])
    return table


def render_main(width, height):
    pixels = np.empty(width * height * 4, dtype=np.float32)

    @worker.launch
    def _(self):
        assert self.table is not None, 'Please APPLY the program first'
        output = self.table['Render Output']
        output.render(pixels, width, height)

    worker.wait_done()
    return pixels


def apply_main():
    @worker.launch
    def _(self):
        self.table = taichi_init()
        output = self.table['On Start']
        output.run()

    worker.wait_done()
    bpy.context.scene.frame_current = 0


@bpy.app.handlers.persistent
def frame_update_callback(*make_the_stupid, **blender_happy):
    if worker is None or worker.table is None:
        return

    @worker.launch
    def _(self):
        output = self.table['On Update']
        output.run()

    worker.wait_done()


worker = None


def register():
    global worker
    worker = TaichiWorker()
    bpy.app.handlers.frame_change_pre.append(frame_update_callback)


def unregister():
    bpy.app.handlers.frame_change_pre.remove(frame_update_callback)
    worker.stop()
