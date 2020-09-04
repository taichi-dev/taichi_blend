try:
    import taichi as ti
except ImportError:
    pass
else:
    import threading
    import sys
    import time
    import io


    class Console(ti.GUI, io.TextIOBase):
        def __init__(self, name='Console', res=(640, 480), **kwargs):
            super().__init__(name, res, **kwargs)
            self.font_color = kwargs.get('font_color', 0xffffff)
            self.font_size = kwargs.get('font_size', 16)
            self.fps_limit = None
            self.content = ''
            self.prev_stream = None

        def show(self):
            content = self.content + '_'
            lines = content.splitlines()
            while len(lines) > self.res[1] // self.font_size:
                lines.pop(0)
            for i, line in enumerate(lines):
                pos = (0, 1 - i * self.font_size / self.res[1])
                self.text(line, pos, font_size=self.font_size, color=self.font_color)
            super().show()

        def pre_frame(self):
            pass

        def mainloop(self):
            while self.running:
                last_time = time.time()
                self.pre_frame()
                self.show()
                time.sleep(1 / 20)
            self.core = None

        def start(self):
            t = threading.Thread(target=self.mainloop)
            t.start()

        def write(self, s):
            self.prev_stream.write(s)
            self.content += s


    def open_console(*args, **kwargs):
        if not hasattr(open_console, 'cons') or open_console.cons.core is None:
            open_console.cons = Console(*args, **kwargs)
            open_console.cons.prev_stream = sys.stdout
            sys.stdout = open_console.cons
            sys.stderr = open_console.cons
            open_console.cons.start()
        return open_console.cons
