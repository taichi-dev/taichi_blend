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
        self.output = None

    def stop(self):
        print('Stopping worker')
        if self.running:
            self.running = False
            self.q.put((lambda self: None, [None, None]), block=False)

    def main(self):
        print('Worker started')
        while self.running:
            try:
                func, resptr = self.q.get(block=True, timeout=1)
            except queue.Empty:
                continue

            try:
                func(self)
            except Exception:
                msg = traceback.format_exc()
                print('Exception while running task:\n' + msg)
                resptr[0] = msg

            self.q.task_done()

    def launch(self, func):
        resptr = [None, None]
        self.q.put((func, resptr), block=True, timeout=None)
        return resptr

    def wait_done(self):
        self.q.join()


def taichi_init():
    import taichi as ti
    backend = bpy.context.scene.taichi_use_backend.lower()
    ti.init(arch=getattr(ti, backend))

    name = bpy.context.scene.taichi_node_group
    table = utils.get_node_table(bpy.data.node_groups[name])

    stdout = bpy.context.scene.taichi_stdout_text
    if stdout in bpy.data.texts:
        import sys
        stdout = bpy.data.texts[stdout]
        stdout.clear()
        sys.stdout = stdout
        sys.stderr = stdout

    return table


def render_main(width, height, region3d):
    pixels = np.empty(width * height * 4, dtype=np.float32)

    @worker.launch
    def result(self):
        assert self.table is not None, 'Please APPLY the program first'
        if 'Render Inputs' in self.table:
            inputs = self.table['Render Inputs']
            inputs.set_region_data(region3d)
        if 'Render Output' in self.table:
            output = self.table['Render Output']
            output.render(pixels, width, height)
        else:
            raise ValueError('No render output node!')

    worker.wait_done()

    return pixels


def apply_main(ui):
    @worker.launch
    def result(self):
        self.table = taichi_init()
        self.output = None
        for name in ['Output Tasks', 'Output Mesh Animation']:
            if name in self.table:
                self.output = self.table[name]
                break
        else:
            raise ValueError('No output node!')

        self.output.start.run()

    worker.wait_done()
    if result[0] is not None:
        ui.report({'ERROR'}, result[0])
    else:
        ui.report({'INFO'}, 'Taichi program applied')

    bpy.context.scene.frame_current = bpy.context.scene.frame_start


@bpy.app.handlers.persistent
def frame_update_callback(*args):
    if worker is None or worker.output is None:
        return

    @worker.launch
    def result(self):
        self.output.update.run()

    worker.wait_done()


worker = None


def register():
    global worker
    worker = TaichiWorker()
    bpy.app.handlers.frame_change_pre.append(frame_update_callback)


def unregister():
    bpy.app.handlers.frame_change_pre.remove(frame_update_callback)
    worker.stop()
