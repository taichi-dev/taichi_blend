from tina import *
import bpy


@A.register
class TestOutput(IRun):
    '''
    Name: test_output
    Category: output
    Inputs: task:t
    Output:
    '''
    def __init__(self, task):
        assert isinstance(task, IRun)
        self.task = task

    def run(self):
        self.task.run()


@A.register
@ti.data_oriented
class RenderOutput:
    '''
    Name: render_output
    Category: output
    Inputs: image:vf
    Output:
    '''
    def __init__(self, img):
        assert isinstance(img, IField)

        self.img = img

    def _cook(self, color):
        if isinstance(color, ti.Expr):
            color = ti.Vector([color, color, color])
        elif isinstance(color, ti.Matrix):
            assert color.m == 1, color.m
            if color.n == 1:
                color = ti.Vector([color(0), color(0), color(0)])
            elif color.n == 2:
                color = ti.Vector([color(0), color(1), 0])
            elif color.n in [3, 4]:
                color = ti.Vector([color(0), color(1), color(2)])
            else:
                assert False, color.n
        return color

    @ti.func
    def image_at(self, i, j, width, height):
        ti.static_assert(len(self.img.meta.shape) == 2)
        scale = ti.Vector(self.img.meta.shape) / ti.Vector([width, height])
        pos = ti.Vector([i, j]) * scale
        color = bilerp(self.img, pos)
        return self._cook(color)

    @ti.kernel
    def render(self, out: ti.ext_arr(), width: int, height: int):
        for i, j in ti.ndrange(width, height):
            r, g, b = self.image_at(i, j, width, height)
            base = (j * width + i) * 4
            out[base + 0] = r
            out[base + 1] = g
            out[base + 2] = b
            out[base + 3] = 1
