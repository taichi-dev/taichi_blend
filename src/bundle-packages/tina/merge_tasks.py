from . import *


@A.register
class Def(IRun):
    '''
    Name: merge_tasks
    Category: misc
    Inputs: *tasks:t
    Output: merged:t
    '''

    def __init__(self, *tasks):
        assert all(isinstance(t, IRun) for t in tasks)

        self.tasks = tasks

    def run(self):
        for t in self.tasks:
            t.run()


