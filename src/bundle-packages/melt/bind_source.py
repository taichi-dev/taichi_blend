from . import *


@A.register
def Def(buf, src):
    '''
    Name: bind_source
    Category: storage
    Inputs: double:cf source:f
    Output: double:cf
    '''
    assert isinstance(buf, A.double_buffer)
    assert isinstance(src, IField)

    buf.src = src
    return buf
