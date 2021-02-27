from . import *


@A.register
class Def(IRun):
    '''
    Name: copy_field
    Category: storage
    Inputs: source:f dest:cf
    Output: task:t
    '''

    def ns_convert(src, dst):
        return dst, src

    def __init__(self, dst, src):
        assert isinstance(dst, IField)
        assert isinstance(src, IField)

        self.dst = dst
        self.src = src

    @ti.kernel
    def run(self):
        for I in ti.static(self.dst):
            self.dst[I] = self.src[I]


