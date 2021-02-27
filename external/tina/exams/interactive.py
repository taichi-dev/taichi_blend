from tina.things import *
from tina.engine.path import *
from tina.tools.control import CamControl
from tina.tools.readgltf import readgltf


ti.init(ti.opengl)
init_things()
PathEngine()
FilmTable().set_size(512, 512)

vertices, mtlids, materials, images = readgltf('assets/cornell.gltf')
ModelPool().load(vertices, mtlids)
MaterialPool().load(materials)
ImagePool().load(images)
BVHTree().build()

gui = ti.GUI()
gui.control = CamControl(gui)
while gui.running:
    if gui.control.process_events():
        FilmTable().clear()
    Camera().set_perspective(gui.control.get_perspective())
    PathEngine().render()
    gui.set_image(FilmTable().get_image())
    gui.show()
