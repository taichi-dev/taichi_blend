from . import *


@A.register
def Def(buf, src):
    '''
    Name: bind_source
    Category: storage
    Inputs: double:f source:f
    Output: double:f
    '''
    assert isinstance(buf, A.double_buffer)
    assert isinstance(src, IField)

    buf.src = src
    return buf
