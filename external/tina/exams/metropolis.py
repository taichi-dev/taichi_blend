from tina.things import *
from tina.engine.mltpath import *
from tina.tools.control import CamControl
from tina.tools.readgltf import readgltf


ti.init(ti.opengl)
init_things()
#PathEngine()
MLTPathEngine()
FilmTable().set_size(512, 512)

#vertices, mtlids, materials, images = readgltf('assets/caustics.gltf')
vertices, mtlids, materials, images = readgltf('assets/cornell.gltf')
ModelPool().load(vertices, mtlids)
MaterialPool().load(materials)
ImagePool().load(images)
BVHTree().build()

#LightPool().pos[0] = [0, 6.7, 0]

gui = ti.GUI()
gui.control = CamControl(gui)

gui.LSP = gui.slider('LSP', 0, 1)
gui.LSP.value = MLTPathEngine().LSP[None]
gui.Sigma = gui.slider('Sigma', 0, 0.5)
gui.Sigma.value = MLTPathEngine().Sigma[None]

while gui.running:
    if gui.control.process_events():
        FilmTable().clear()
        MLTPathEngine().reset()
    Camera().set_perspective(gui.control.get_perspective())

    #Camera().set_perspective(np.array([[ 1.62719111e+00, -9.27462974e-17, -5.93505772e-01, -8.91657993e-01], [-4.42200055e-01,  1.15526485e+00, -1.21236226e+00, -1.95648689e+00], [-2.28597834e-01, -7.45213483e-01, -6.26737565e-01, 2.84053540e+00], [-2.28552119e-01, -7.45064455e-01, -6.26612230e-01, 2.93995736e+00]]))

    MLTPathEngine().LSP[None] = gui.LSP.value
    MLTPathEngine().Sigma[None] = gui.Sigma.value

    MLTPathEngine().render()
    #PathEngine().render()
    img = FilmTable().get_image()
    img = ti.imresize(img**(1/2.2), 512)
    gui.set_image(img)
    gui.show()
