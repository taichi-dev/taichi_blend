from . import *


@A.register
class Def(IRun):
    '''
    Name: static_print
    Category: output
    Inputs: value:a
    Output: task:t
    '''

    def __init__(self, value):
        self.value = value

    def run(self):
        print(self.value)
