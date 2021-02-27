from tina.things import *
from tina.engine.path import *
from tina.tools.readgltf import readgltf
import time


ti.init(ti.cuda)
init_things()
PathEngine()
FilmTable().set_size(512, 512)

vertices, mtlids, materials, images = readgltf('assets/monkey_cornell.gltf')
ModelPool().load(vertices, mtlids)
MaterialPool().load(materials)
ImagePool().load(images)
BVHTree().build()

Camera().set_perspective(np.array([
            [ 1.73205081e+00,  0.00000000e+00,  0.00000000e+00,  1.01348227e-02],
            [ 0.00000000e+00,  1.73205081e+00, -1.73205081e-05, -3.36860025e+00],
            [ 0.00000000e+00, -1.00020002e-05, -1.00020002e+00,  5.27350023e+00],
            [ 0.00000000e+00, -1.00000000e-05, -1.00000000e+00,  5.37243564e+00],
            ]))

PathEngine().render()
FilmTable().get_image()
FilmTable().clear()

t0 = time.time()
nsamples = 32
for i in range(nsamples):
    print(i, 'samples...')
    PathEngine().render()

img = FilmTable().get_image()
title = f'{nsamples / (time.time() - t0):.03f} sps'
ti.imshow(img, title)
print(title)
