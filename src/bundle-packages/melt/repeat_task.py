from . import *


@A.register
class Def(IRun):
    '''
    Name: repeat_task
    Category: misc
    Inputs: task:t times:i
    Output: repeated:t
    '''

    def __init__(self, task, times):
        assert isinstance(task, IRun)

        self.task = task
        self.times = times

    def run(self):
        for i in range(self.times):
            self.task.run()


