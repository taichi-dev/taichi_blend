from . import *


@A.register
class Def(IField):
    '''
    Name: pack_vector
    Category: converter
    Inputs: *comps:f
    Output: vector:vf
    '''

    def __init__(self, *args):
        assert all(isinstance(a, IField) for a in args)

        self.args = args
        if len(self.args):
            self.meta = FMeta(self.args[0])

    @ti.func
    def _subscript(self, I):
        args = [a[I] for a in self.args]
        return vconcat(*args)


