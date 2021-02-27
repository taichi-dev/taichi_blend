'''
encoding large numpy arrays into base64 for embed assets
'''

import numpy as np
from base64 import b85encode, b85decode
from io import BytesIO


def encode_numpy_array(arr, compress=True):
    with BytesIO() as f:
        if compress:
            np.savez_compressed(f, arr)
        else:
            np.savez(f, arr)
        bs = f.getvalue()

    bs = b85encode(bs)
    return bs


def decode_numpy_array(bs):
    bs = b85decode(bs)
    with BytesIO(bs) as f:
        arr = np.load(f)['arr_0']
    return arr



def encode_numpy_array_embed(arr, linewidth=1024):
    decoder = "(lambda bs: (lambda f: [__import__('numpy').load(f)['arr_0'], f.close()][0])(__import__('io').BytesIO(__import__('base64').b85decode(bs))))"
    bs = encode_numpy_array(arr)
    rs = '\n'
    for pos in range(0, len(bs), linewidth):
        rs += repr(bs[pos:pos + linewidth]) + '\n'
    return f'({decoder}({rs}))'


__all__ = [
        'encode_numpy_array',
        'decode_numpy_array',
        'encode_numpy_array_embed',
]


if __name__ == '__main__':
    from tina_sobol import load_standard_sobol_file
    arr = load_standard_sobol_file('/home/bate/Downloads/new-joe-kuo-6.21201')
    arr = arr.astype(np.uint32)
    embed = encode_numpy_array_embed(arr)
    with open('/tmp/sobol_data.py', 'w') as f:
        f.write('_sobol_data = \\\n')
        f.write(embed)
        f.write('.astype(int)\n')
