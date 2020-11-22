from . import *

import os.path


@A.register
class Def(IField, IRun):
    '''
    Name: disk_frame_cache
    Category: storage
    Inputs: path:s prefix:s format:fmt field:f update:t
    Output: cached:f update:t
    '''

    def ns_convert(*args):
        import bpy
        return (*args, lambda: bpy.context.scene.frame_current)

    def __init__(self, path, prefix, fmt, buf, update, getframe):
        assert isinstance(buf, IField)

        self.path = path
        self.prefix = prefix
        self.fmt = fmt
        self.buf = buf
        self.meta = FMeta(self.buf)
        self.update = update
        self.getframe = getframe
        self.cached = {}

        if not os.path.exists(path):
            os.mkdir(path)

    def get_path(self, frame):
        return os.path.join(self.path, f'{self.prefix}{frame:04d}.{self.fmt}')

    def file_save(self, path, data):
        if self.fmt == 'npy':
            np.save(path, data)
        elif self.fmt == 'npy.gz':
            import gzip
            with gzip.open(path, 'wb') as f:
                np.save(f, data)
        elif self.fmt == 'npy.xz':
            import lzma
            with lzma.LZMAFile(path, 'wb') as f:
                np.save(f, data)
        elif self.fmt in ['png', 'jpg', 'bmp']:
            ti.imwrite(data, path)
        elif self.fmt == 'none':
            pass
        else:
            assert False, self.fmt

    def file_load(self, path):
        if self.fmt == 'npy':
            return np.load(path)
        elif self.fmt == 'npy.gz':
            import gzip
            with gzip.open(path, 'rb') as f:
                np.load(f)
        elif self.fmt == 'npy.xz':
            import lzma
            with lzma.LZMAFile(path, 'rb') as f:
                np.load(f)
        elif self.fmt in ['png', 'jpg', 'bmp']:
            return ti.imread(data)
        else:
            assert False, self.fmt

    def write_disk(self, frame, data):
        self.cached[frame] = data

        path = self.get_path(frame)
        self.file_save(path, data)

    def read_disk(self, frame):
        if frame in self.cached:
            return self.cached[frame]

        path = self.get_path(frame)
        if os.path.exists(path):
            return self.file_load(path)

        return None

    def get_cache(self, frame):
        data = self.read_disk(frame)
        if data is not None:
            self.buf.from_numpy(data)
            return data

        self.update.run()
        data = self.buf.to_numpy()
        self.write_disk(frame, data)
        return data

    def run(self):
        frame = self.getframe()
        data = self.get_cache(frame)

    @ti.func
    def _subscript(self, I):
        return self.buf[I]
