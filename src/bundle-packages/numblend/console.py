try:
    import tkinter
except ImportError:
    print('WARNING: numblend cannot import tkinter! nb.open_console will be unavailable')
    open_console = NotImplemented
else:
    import io
    import sys
    import time
    import threading


    class Console(io.TextIOBase):
        def __init__(self, res=(640, 480), **kwargs):
            super().__init__()
            self.prev_stream = None
            self.root = tkinter.Tk()
            self.log = tkinter.Text(self.root)
            self.log.grid(row=25, column=0, columnspan=80)

        def mainloop(self):
            self.root.mainloop()

        def write(self, s):
            if self.prev_stream is not None:
                self.prev_stream.write(s)
            self.log.insert(tkinter.END, s)


    def open_console(*args, **kwargs):
        if not hasattr(open_console, 'cons') or open_console.cons.core is None:
            open_console.cons = Console(*args, **kwargs)
            open_console.cons.prev_stream = sys.stdout
            sys.stdout = open_console.cons
            sys.stderr = open_console.cons
        return open_console.cons


    if __name__ == '__main__':
        cons = open_console()
        print('hello', end='')
        print('workd\nas\n')
        cons.mainloop()