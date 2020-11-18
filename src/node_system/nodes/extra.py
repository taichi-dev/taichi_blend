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
    def __init__(self, image, update):
        assert isinstance(image, IField)
        assert isinstance(update, IRun)

        raise NotImplementedError

    def run(self):
        raise NotImplementedError
