from .utils import *


@ti.data_oriented
class INode:
    pass


class NodeSystem:
    type2socket = {
            'm': 'meta',
            'f': 'field',
            'cf': 'cached_field',
            'vf': 'vector_field',
            'n': 'callable',
            'x': 'matrix',
            't': 'task',
            'a': 'any',
    }
    type2option = {
            'i': 'int',
            'c': 'float',
            'b': 'bool',
            's': 'str',
            'dt': 'enum',
            'fmt': 'enum',
            'so': 'search_object',
            'i2': 'vec_int_2',
            'i3': 'vec_int_3',
            'c2': 'vec_float_2',
            'c3': 'vec_float_3',
    }
    type2items = {
            'dt': 'float int i8 i16 i32 i64 u8 u16 u32 u64 f32 f64'.split(),
            'fmt': 'npy npy.gz npy.xz png jpg bmp none'.split(),
    }

    def __init__(self):
        self.nodes = {}

    def __getattr__(self, name):
        if name not in self.nodes:
            raise AttributeError(f'Cannot find any node matches name `{name}`')
        return self.nodes[name].original

    def unregister(self, name):
        if name in self.nodes:
            del self.nodes[name]

    def __len__(self):
        return len(self.nodes)

    def register(self, cls):
        docs = cls.__doc__.strip().splitlines()

        node_name = None
        inputs = []
        outputs = []
        category = 'uncategorized'
        converter = getattr(cls, 'ns_convert', lambda *x: x)

        for line in docs:
            line = [l.strip() for l in line.split(':', 1)]
            if line[0] == 'Name':
                node_name = line[1].replace(' ', '_')
            if line[0] == 'Inputs':
                inputs = line[1].split()
            if line[0] == 'Output':
                outputs = line[1].split()
            if line[0] == 'Category':
                category = line[1]

        if node_name in self.nodes:
            raise KeyError(f'Node with name `{node_name}` already registered')

        cls.__name__ = node_name

        class Def:
            pass

        if len(inputs):
            name, type = inputs[-1].split(':', 1)
            if name.startswith('*') and name.endswith('s'):
                name = name[1:-1]
                inputs.pop()
                for i in range(2):
                    inputs.append(f'{name}{i}:{type}')

        lut = []
        omap = []
        iopt, isoc = 0, 0
        for i, arg in enumerate(inputs):
            name, type = arg.split(':', 1)
            if type in self.type2option:
                option = self.type2option[type]
                lut.append((True, iopt))
                iopt += 1
                setattr(Def, f'option_{iopt}', (name, option))
                if option == 'enum':
                    items = tuple(self.type2items[type])
                    setattr(Def, f'items_{iopt}', items)
            else:
                socket = self.type2socket[type]
                lut.append((False, isoc))
                isoc += 1
                setattr(Def, f'input_{isoc}', (name, socket))

        for i, arg in enumerate(outputs):
            name, type = arg.split(':', 1)
            if type.endswith('%'):
                type = type[:-1]
                omap.append(name)
            else:
                omap.append(None)
            socket = self.type2socket[type]
            setattr(Def, f'output_{i + 1}', (name, socket))

        def wrapped(self, inputs, options):
            # print('+++', inputs, options)
            args = []
            for isopt, index in lut:
                if isopt:
                    args.append(options[index])
                else:
                    args.append(inputs[index])
            # print('===', cls, args)
            args = converter(*args)
            try:
                ret = cls(*args)
            except Exception as e:
                print(f'Exception while constructing node `{node_name}`!')
                raise e
            rets = []
            for name in omap:
                if name is None:
                    rets.append(ret)
                else:
                    rets.append(getattr(ret, name, NotImplemented))
            # print('---', cls, rets)
            return ret, tuple(rets)

        setattr(Def, 'category', category)
        setattr(Def, 'wrapped', wrapped)
        setattr(Def, 'original', cls)

        self.nodes[node_name] = Def

        return cls
