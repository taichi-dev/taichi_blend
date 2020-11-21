from . import *


@A.register
class MEdit(Meta):
    '''
    Name: edit_meta
    Category: meta
    Inputs: meta:m shape:i3 dtype:dt vdims:i2 eshape:b edtype:b evdims:b
    Output: meta:m
    '''

    def ns_convert(meta, shape, dtype, vdims, eshape, edtype, evdims):
        dtype = dtype_from_name(dtype)
        if shape[2] == 0:
            shape = shape[0], shape[1]
        if shape[1] == 0:
            shape = shape[0],
        if shape[0] == 0:
            shape = ()
        if vdims[1] == 0:
            vdims = vdims[0],
        if vdims[0] == 0:
            vdims = ()
        return meta, shape, dtype, vdims, eshape, edtype, evdims

    def __init__(self, meta, shape=None, dtype=None, vdims=None,
            eshape=None, edtype=None, evdims=None):
        if eshape is None:
            eshape = shape is not None
        if edtype is None:
            edtype = dtype is not None
        if evdims is None:
            evdims = vdims is not None

        super().copy(meta)
        if edtype:
            self.dtype = dtype
        if eshape:
            self.shape = totuple(shape)
        if evdims:
            self.vdims = totuple(vdims)


Def = MEdit
