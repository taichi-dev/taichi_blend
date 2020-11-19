import bpy
import queue
import threading
import traceback

from ..node_system.nodes import utils


class TaichiWorker:
    def __init__(self):
        self.q = queue.Queue(maxsize=4)
        self.running = True

        self.t = threading.Thread(target=self.main)
        self.t.daemon = True
        self.t.start()

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


class TaichiApplyOperator(bpy.types.Operator):
    '''Apply Taichi tree'''

    bl_idname = "scene.taichi_apply"
    bl_label = "Apply"

    @classmethod
    def poll(cls, context):
        return bpy.context.scene.taichi_node_group in bpy.data.node_groups

    def execute(self, context):
        @worker.launch
        def _(self):
            import taichi as ti
            backend = bpy.context.scene.taichi_use_backend.lower()
            ti.init(arch=getattr(ti, backend))

            name = bpy.context.scene.taichi_node_group
            table = utils.get_node_table(bpy.data.node_groups[name])
            output = table['Output Task']
            output.run()
            print('Task finished')

        return {'FINISHED'}


class TaichiPanel(bpy.types.Panel):
    '''Taichi options'''

    bl_label = 'Taichi'
    bl_idname = 'SCENE_PT_taichi'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop_search(scene, 'taichi_node_group',
                bpy.data, 'node_groups', text='Tree')
        layout.prop(scene, 'taichi_use_backend')
        layout.operator('scene.taichi_apply')


worker = None


def register():
    global worker
    worker = TaichiWorker()

    bpy.types.Scene.taichi_node_group = bpy.props.StringProperty()
    bpy.types.Scene.taichi_use_backend = bpy.props.EnumProperty(name='Backend',
        items=[(item.upper(), item, '') for item in [
            'CPU', 'GPU', 'Cuda', 'OpenCL', 'OpenGL', 'Metal', 'CC',
            ]])

    bpy.utils.register_class(TaichiApplyOperator)
    bpy.utils.register_class(TaichiPanel)


def unregister():
    bpy.utils.unregister_class(TaichiPanel)
    bpy.utils.unregister_class(TaichiApplyOperator)

    del bpy.types.Scene.taichi_node_group
    del bpy.types.Scene.taichi_use_backend

    worker.stop()
