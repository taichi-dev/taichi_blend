from tina.engine import *
from tina.tools.control import *
from tina.tools.readgltf import readgltf


ti.init(ti.cuda)
Stack()
Camera()
BVHTree()
ImagePool()
ModelPool()
LightPool()
ToneMapping()
MaterialPool()
PathEngine()

LightPool().color[0] = V3(512)
LightPool().pos[0] = V(0, 40, 0)
LightPool().radius[0] = 0.4
LightPool().count[None] = 1

vertices, mtlids, materials = readgltf('assets/cornell.gltf')
#vertices, mtlids, materials = readgltf('/tmp/luxball2.gltf')
ModelPool().load(vertices, mtlids)
MaterialPool().load(materials)

BVHTree().build()

gui = ti.GUI()
gui.control = Control(gui)
while gui.running:
    if gui.control.process_events():
        #PathEngine().normal.clear()
        PathEngine().film.clear()
    Camera().set_perspective(gui.control.get_perspective())
    PathEngine().render()
    #PathEngine().render_aov()
    #gui.set_image(PathEngine().normal.to_numpy_normalized() * 0.5 + 0.5)
    gui.set_image(PathEngine().film.get_image())
    gui.show()
