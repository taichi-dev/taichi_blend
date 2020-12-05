from . import *


@A.register
class Def(IField):
    '''
    Name: specify_meta
    Category: meta
    Inputs: meta:m field:f
    Output: field:f
    '''

    def __init__(self, meta, field):
        assert isinstance(meta, Meta)
        assert isinstance(field, IField)

        self.meta = meta
        self.field = field

    @ti.func
    def _subscript(self, I):
        return self.field[I]
