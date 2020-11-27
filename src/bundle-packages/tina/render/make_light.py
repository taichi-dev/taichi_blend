from . import *


@A.register
class MakeLight(ICall):
    '''
    Name: make_light
    Category: render
    Inputs: world:x color:f
    Output: light:n
    '''

    def __init__(self, world, color):
        self.world = world
        self.color = color

    @ti.func
    def call(self, pos):
        dir, _ = self.world.apply(V(0, 0, 1), 0)
        return dir, self.color[None]
