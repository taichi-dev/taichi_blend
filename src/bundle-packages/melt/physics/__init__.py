from .. import *

@ti.func
def list_subscript(a, i: ti.template()):
    if ti.static(isinstance(i, ti.Expr)):
        k = i
        ret = sum(a) * 0
        for j in ti.static(range(len(a))):
            if k == j:
                ret = a[j]
        return ret
    else:
        return a[i]

from . import basics
from . import mpm88
from . import mciso
from . import mpm
