from . import *


@A.register
class AddShader(ICall):
    '''
    Name: add_shader
    Category: shader
    Inputs: *shaders:n
    Output: merged:n
    '''

    def __init__(self, *shaders):
        assert all(isinstance(shader, ICall) for shader in shaders)

        self.shaders = shaders

    def call(self, *args):
        return sum(shader.call(*args) for shader in self.shaders)
