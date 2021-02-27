'''Blender-NumPy interface'''

import numpy as np
from .common import np_array


def to_numpy(b, key, dim=None):
    dim = dim or len(getattr(b[0], key))
    dim = len(getattr(b[0], key))
    seq = [0] * (len(b) * dim)
    b.foreach_get(key, seq)
    return np.array(seq).reshape(len(b), dim)


def from_numpy(b, key, a, dim=None):
    a = np_array(a)
    if dim is None:
        dim = len(getattr(b[0], key)) if len(b) else a.shape[1]
    assert len(a.shape) == 2
    assert a.shape[1] == dim
    if len(b) < a.shape[0]:
        b.add(a.shape[0] - len(b))
    seq = a.reshape(a.shape[0] * dim).tolist()
    seq = seq + [0] * (len(b) * dim - len(seq))
    b.foreach_set(key, seq)


def matrix_to_numpy(m):
    return np.array([[m[i][j] for j in range(len(m[i]))] for i in range(len(m))])
