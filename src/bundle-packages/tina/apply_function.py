from . import *


@A.register
class Def(IField):
    '''
    Name: apply_function
    Category: converter
    Inputs: func:s *args:f
    Output: result:f
    '''

    def ns_convert(func, *args):
        for name in 'print min max int float any all'.split():
            func = func.replace(name, 'ti.ti_' + name)
        func = eval(f'lambda x, y: ({func})')
        return (func, *args)

    def __init__(self, func, *args):
        assert all(isinstance(a, IField) for a in args)

        self.func = func
        self.args = args
        if len(self.args):
            self.meta = FMeta(self.args[0])

    @ti.func
    def _subscript(self, I):
        return self.func(*[a[I] for a in self.args])


