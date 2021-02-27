'''
dynamic memory allocator, mainly used for textures
'''


class MemoryAllocator:
    def __init__(self, size):
        self.size = size
        self.reset()

    def reset(self):
        self.free_chunk = [(0, self.size)]
        self.used_chunk = []

    def malloc(self, size):
        for i, (chk_base, chk_size) in enumerate(self.free_chunk):
            if chk_size >= size:
                del self.free_chunk[i]
                if chk_size != size:
                    rest_chunk = (chk_base + size, chk_size - size)
                    self.free_chunk.insert(i, rest_chunk)
                base = chk_base
                break
        else:
            raise RuntimeError('Out of memory!')
        self.used_chunk.append((base, size))
        return base

    def free(self, base):
        for i, (chk_base, chk_size) in enumerate(self.used_chunk):
            if chk_base == base:
                del self.used_chunk[i]
                size = chk_size
                break
        else:
            raise RuntimeError(f'Invalid pointer: {base!r}')

        new_chunk = (base, size)
        self.free_chunk.insert(i, new_chunk)


class IdAllocator:
    def __init__(self, count):
        self.count = count
        self.reset()

    def reset(self):
        self.water = 0

    def malloc(self):
        id = self.water
        if id >= self.count:
            raise RuntimeError('Out of ID!')
        self.water += 1
        return id

    def free(self, id):
        pass
