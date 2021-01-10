import bpy
import numpy as np


def taichi_init():
    import taichi as ti
    backend = bpy.context.scene.taichi_use_backend.lower()
    ti.init(arch=getattr(ti, backend), make_block_local=False)

    from melt.blender import get_node_table
    name = bpy.context.scene.taichi_node_group
    table = get_node_table(bpy.data.node_groups[name])

    stdout = bpy.context.scene.taichi_stdout_text
    if stdout in bpy.data.texts:
        import sys
        stdout = bpy.data.texts[stdout]
        stdout.clear()
        sys.stdout = stdout
        sys.stderr = stdout

    return table


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
    from taichi_worker import TaichiWorker
    worker = TaichiWorker()
    worker.table = None
    worker.output = None
    bpy.app.handlers.frame_change_pre.append(frame_update_callback)


def unregister():
    bpy.app.handlers.frame_change_pre.remove(frame_update_callback)
    worker.stop()
    worker = None
