from . import *


@A.register
class Def(IField):
    '''
    Name: chessboard_texture
    Category: texture
    Inputs: size:i
    Output: sample:f
    '''

    def __init__(self, size):
        self.size = size

    @ti.func
    def _subscript(self, I):
        return (I // self.size).sum() % 2


