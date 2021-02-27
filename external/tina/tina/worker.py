'''
unified API interface for running in a separate worker thread
'''

from tina.things import *
#from tina.engine.mltpath import MLTPathEngine as DefaultEngine
from tina.engine.path import PathEngine as DefaultEngine
from tina.engine.preview import PreviewEngine


def init():
    ti.init(ti.cuda, device_memory_fraction=0.8)
    init_things()
    DefaultEngine()
    PreviewEngine()


def synchronize():
    ti.sync()


def render(aa=True):
    DefaultEngine().render()


def render_preview(aa=True):
    PreviewEngine().render()


def set_size(nx, ny):
    FilmTable().set_size(nx, ny)


def get_size():
    return FilmTable().nx, FilmTable().ny


def clear(id=0):
    if hasattr(DefaultEngine(), 'reset'):
        DefaultEngine().reset()
    FilmTable().clear(id)


def set_mlt_param(lsp, sigma):
    if hasattr(DefaultEngine(), 'LSP'):
        DefaultEngine().LSP[None] = lsp
    if hasattr(DefaultEngine(), 'Sigma'):
        DefaultEngine().Sigma[None] = sigma


def get_image(id=0):
    return FilmTable().get_image(id)


def fast_export_image(pixels, id=0):
    FilmTable().fast_export_image(pixels, id)


def clear_lights():
    LightPool().clear()


def set_world_light(fac, tex):
    WorldLight().set(fac, tex)


def add_light(world, color, size, type):
    LightPool().add(world, color, size, type)


def load_model(vertices, mtlids):
    ModelPool().load(vertices, mtlids)


def load_images(images):
    ImagePool().load(images)


def load_materials(materials):
    MaterialPool().load(materials)


def build_tree():
    BVHTree().build()


def set_camera(pers):
    Camera().set_perspective(pers)
