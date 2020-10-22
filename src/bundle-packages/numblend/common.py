'''Common utilities'''

import numpy as np


def np_array(x):
    if x is not None and not isinstance(x, np.ndarray):
        x = np.array(x)
    return x
