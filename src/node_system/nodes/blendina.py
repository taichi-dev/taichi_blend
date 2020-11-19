from tina import *
import bpy


@A.register
class OutputTask(IRun):
    '''
    Name: output_task
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
class ViewportVisualize(IRun):
    '''
    Name: viewport_visualize
    Category: output
    Inputs: image:vf update:t
    Output: task:t
    '''
    def __init__(self, img, update):
        assert isinstance(img, IField)
        assert isinstance(update, IRun)

        self.img = img
        self.update = update

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
    def image_at(self, i, j):
        ti.static_assert(len(self.img.meta.shape) == 2)
        scale = ti.Vector(self.img.meta.shape) / ti.Vector(self.res)
        pos = ti.Vector([i, j]) * scale
        color = bilerp(self.img, pos)
        return self._cook(color)

    @ti.kernel
    def render(self, out: ti.ext_arr(), width: int, height: int):
        for i, j in ti.ndrange(width, height):
            image_at()

    def run(self):
        raise NotImplementedError
