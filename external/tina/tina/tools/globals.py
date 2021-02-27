'''
declaring global parameters for debugging purpose
'''

from tina.common import *


@ti.data_oriented
class Globals(metaclass=Singleton):
    def __init__(self):
        self.values = {}
        self.sliders = {}
        self.gui_callbacks = []

    @ti.python_scope
    def add(self, name, initial=0, xmin=0, xmax=1, step=0.01):
        self.values[name] = ti.field(float, ())

        @self.gui_callbacks.append
        def gui_callback(gui):
            self.sliders[name] = gui.slider(name, xmin, xmax, step)
            self.sliders[name].value = initial

        @ti.materialize_callback
        def init_val():
            self.values[name][None] = initial

        return self

    @ti.pyfunc
    def get(self, name):
        return self.values[name][None]

    def update(self, gui):
        for callback in self.gui_callbacks:
            callback(gui)
        self.gui_callbacks.clear()
        for name in self.sliders:
            self.values[name][None] = self.sliders[name].value

    def __getattr__(self, name):
        return self.get(name)
