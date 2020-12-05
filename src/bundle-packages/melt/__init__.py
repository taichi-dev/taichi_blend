from .utils import *
from .nodesys import INode, NodeSystem


print('[Melt] Start loading node system...')

A = NodeSystem()


from . import make_meta
from .make_meta import Meta, C


class IRun(INode):
    def __init__(self, chain):
        self.chain = chain

    def run(self):
        self.chain.run()
        self._run()

    def _run(self):
        raise NotImplementedError


class ICall:
    def call(self, *args):
        raise NotImplementedError


class IField(INode):
    is_taichi_class = True

    meta = Meta()

    @ti.func
    def _subscript(self, I):
        raise NotImplementedError

    def subscript(self, *indices):
        I = tovector(indices)
        return self._subscript(I)

    @ti.func
    def __iter__(self):
        if ti.static(self.meta.store is not None):
            for I in ti.static(self.meta.store):
                yield I
        else:
            for I in ti.grouped(ti.ndrange(*self.meta.shape)):
                yield I

    @ti.kernel
    def _to_numpy(self, arr: ti.ext_arr()):
        for I in ti.static(self):
            val = self[I]
            if ti.static(not isinstance(val, ti.Matrix)):
                arr[I] = val
            elif ti.static(val.m == 1):
                for j in ti.static(range(val.n)):
                    arr[I, j] = val[j]
            else:
                raise NotImplementedError

    def to_numpy(self):
        shape = tuple(self.meta.shape) + tuple(self.meta.vdims)
        dtype = self.meta.dtype
        if dtype is int:
            dtype = ti.get_runtime().default_ip
        elif dtype is float:
            dtype = ti.get_runtime().default_fp
        dtype = to_numpy_type(dtype)
        arr = np.empty(shape, dtype=dtype)
        self._to_numpy(arr)
        return arr

    @ti.kernel
    def _from_numpy(self, arr: ti.ext_arr()):
        for I in ti.static(self):
            val = ti.static(ti.subscript(self, I))
            if ti.static(not isinstance(val, ti.Matrix)):
                val = arr[I]
            elif ti.static(val.m == 1):
                for j in ti.static(range(val.n)):
                    val[j] = arr[I, j]
            else:
                raise NotImplementedError

    def from_numpy(self, arr):
        assert isinstance(arr, np.ndarray), type(arr)
        shape = tuple(self.meta.shape) + tuple(self.meta.vdims)
        dtype = to_numpy_type(self.meta.dtype)
        assert arr.shape == shape, (arr.shape, shape)
        assert arr.dtype == dtype, (arr.dtype, dtype)
        self._from_numpy(arr)

    def __str__(self):
        return str(self.to_numpy())


from . import get_meta
from .get_meta import FMeta
from . import edit_meta
from .edit_meta import MEdit
from . import specify_meta
from . import field_storage
from .field_storage import Field
from . import dynamic_field
from .dynamic_field import DynamicField
from . import cache_field
from . import double_buffer
from . import bind_source
from . import const_field
from . import uniform_field
from . import flatten_field
from . import disk_frame_cache
from . import clamp_sample
from . import repeat_sample 
from . import boundary_sample
from . import mix_value
from . import lerp_value
from . import map_range
from . import multiply_value
from . import custom_function
from . import vector_component
from . import vector_length
from . import pack_vector
from . import field_index
from . import field_shuffle
from . import field_bilerp
from . import chessboard_texture
from . import random_generator
from . import gaussian_dist
from . import field_laplacian
from . import field_gradient
from . import copy_field
from . import merge_tasks
from . import repeat_task
from . import null_task
from . import canvas_visualize
from . import static_print
from . import physics


print(f'[Melt] Node system loaded: {len(A)} nodes')


__all__ = ['ti', 'A', 'C', 'V', 'np', 'IRun', 'IField', 'Meta', 'MEdit',
        'Field', 'DynamicField', 'ICall', 'FMeta', 'INode', 'clamp',
        'bilerp', 'totuple', 'tovector', 'to_numpy_type']
