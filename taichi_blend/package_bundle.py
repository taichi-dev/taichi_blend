import sys
import os


bundle_path = os.path.join(os.path.dirname(__file__), 'bundle-packages')


def register():
    print('Taichi-Blend package bundle at', bundle_path)
    assert os.path.exists(bundle_path), f'{bundle_path} does not exist!'
    if bundle_path not in sys.path:
        sys.path.insert(0, bundle_path)


def unregister():
    if bundle_path in sys.path:
        sys.path.remove(bundle_path)
