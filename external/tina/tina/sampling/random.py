'''
Taichi built-in pseudo-random generator: ti.random()
'''

from tina.sampling import *


@ti.data_oriented
class RandomSampler(metaclass=Singleton):
    def __init__(self):
        pass

    @ti.func
    def get_proxy(self, i):
        return ti

    def update(self):
        pass

    def reset(self):
        pass
