from tina.image import *


@ti.data_oriented
class ToneMapping(metaclass=Singleton):
    def __init__(self):
        self.exposure = ti.field(float, ())
        self.gamma = ti.field(float, ())

        @ti.materialize_callback
        def init_tonemap():
            self.exposure[None] = 0.3
            self.gamma[None] = 1/2.2

    @ti.func
    def __call__(self, hdr):
        rgb = self.exposure[None] * hdr
        return pow(rgb / (rgb + 0.155) * 1.019, self.gamma[None])
