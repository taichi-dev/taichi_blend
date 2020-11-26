from . import *


@A.register
class MEdit(Meta):
    '''
    Name: edit_meta
    Category: meta
    Inputs: meta:m shape:i3 dtype:dt store:cf vdims:i2 eshape:b edtype:b evdims:b estore:b
    Output: meta:m
    '''

    def ns_convert(meta, shape, dtype, vdims, store, eshape, edtype, evdims, estore):
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
        return meta, shape, dtype, vdims, store, eshape, edtype, evdims, estore

    def __init__(self, meta, shape=None, dtype=None, vdims=None, store=None,
            eshape=None, edtype=None, evdims=None, estore=None):
        if eshape is None:
            eshape = shape is not None
        if edtype is None:
            edtype = dtype is not None
        if evdims is None:
            evdims = vdims is not None
        if estore is None:
            estore = store is not None

        super().copy(meta)
        if edtype:
            self.dtype = dtype
        if eshape:
            self.shape = totuple(shape)
        if evdims:
            self.vdims = totuple(vdims)
        if estore:
            self.store = store


Def = MEdit
