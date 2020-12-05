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
            self.meta = Meta()
            self.meta.copy(self.args[0].meta)
            total = 0
            for arg in self.args:
                n = 1
                if len(arg.meta.vdims):
                    n = arg.meta.vdims[0]
                total += n
            self.meta.vdims = (total,)

    @ti.func
    def _subscript(self, I):
        args = [a[I] for a in self.args]
        return vconcat(*args)


