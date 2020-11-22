import taichi as ti
import os

images = []
frames = 0
while True:
    file = f'{frames + 1:04d}.png'
    if not os.path.exists(file):
        break
    print('Loading', file)
    images.append(ti.imread(file))
    frames += 1

res = images[0].shape[:2]
gui = ti.GUI('imseqshow', res)
while gui.running:
    gui.set_image(images[gui.frame % frames])
    gui.show()
