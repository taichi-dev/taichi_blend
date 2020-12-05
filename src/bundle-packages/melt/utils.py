import taichi as ti
import numpy as np


setattr(ti, 'static', lambda x, *xs: [x] + list(xs) if xs else x) or setattr(
        ti.Matrix, 'element_wise_writeback_binary', (lambda f: lambda x, y, z:
        (y.__name__ != 'assign' or not setattr(y, '__name__', '_assign'))
        and f(x, y, z))(ti.Matrix.element_wise_writeback_binary)) or setattr(
        ti.Matrix, 'is_global', (lambda f: lambda x: len(x) and f(x))(
        ti.Matrix.is_global))


ti.smart = lambda x: x

@eval('lambda x: x()')
def _():
    import copy, ast
    from taichi.lang.transformer import ASTTransformerBase, ASTTransformerPreprocess

    old_get_decorator = ASTTransformerBase.get_decorator

    @staticmethod
    def get_decorator(node):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and isinstance(
                    node.func.value, ast.Name) and node.func.value.id == 'ti'
                and node.func.attr in ['smart']):
            return old_get_decorator(node)
        return node.func.attr

    ASTTransformerBase.get_decorator = get_decorator

    old_visit_struct_for = ASTTransformerPreprocess.visit_struct_for

    def visit_struct_for(self, node, is_grouped):
        if not is_grouped:
            decorator = self.get_decorator(node.iter)
            if decorator == 'smart':  # so smart!
                self.current_control_scope().append('smart')
                self.generic_visit(node, ['body'])
                t = self.parse_stmt('if 1: pass; del a')
                t.body[0] = node
                target = copy.deepcopy(node.target)
                target.ctx = ast.Del()
                if isinstance(target, ast.Tuple):
                    for tar in target.elts:
                        tar.ctx = ast.Del()
                t.body[-1].targets = [target]
                return t

        return old_visit_struct_for(self, node, is_grouped)

    ASTTransformerPreprocess.visit_struct_for = visit_struct_for


def V(*xs):
    return ti.Vector(xs)


def totuple(x):
    if x is None:
        x = []
    if isinstance(x, ti.Matrix):
        x = x.entries
    if isinstance(x, list):
        x = tuple(x)
    if not isinstance(x, tuple):
        x = x,
    if isinstance(x, tuple) and len(x) and x[0] is None:
        x = []
    return x


def tovector(x):
    return ti.Vector(totuple(x))


def vconcat(*xs):
    res = []
    for x in xs:
        if isinstance(x, ti.Matrix):
            res.extend(x.entries)
        else:
            res.append(x)
    return ti.Vector(res)


@ti.func
def clamp(x, xmin, xmax):
    return min(xmax, max(xmin, x))


@ti.func
def bilerp(f: ti.template(), pos):
    p = float(pos)
    I = int(ti.floor(p))
    x = p - I
    y = 1 - x
    ti.static_assert(len(f.meta.shape) == 2)
    return (f[I + V(1, 1)] * x[0] * x[1] +
            f[I + V(1, 0)] * x[0] * y[1] +
            f[I + V(0, 0)] * y[0] * y[1] +
            f[I + V(0, 1)] * y[0] * x[1])


def dtype_from_name(name):
    dtypes = 'i8 i16 i32 i64 u8 u16 u32 u64 f32 f64'.split()
    if name in dtypes:
        return getattr(ti, name)
    if name == 'float':
        return float
    if name == 'int':
        return int
    assert False, name


def to_numpy_type(dtype):
    if dtype is int:
        dtype = ti.get_runtime().default_ip
    elif dtype is float:
        dtype = ti.get_runtime().default_fp
    return ti.to_numpy_type(dtype)
