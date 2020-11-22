import sys
import platform
major = sys.version_info.major
minor = sys.version_info.minor
assert major == 3 and minor in [6, 7, 8], "Only Python 3.6/3.7/3.8 is supported"

ver = str(major) + str(minor)
plat = sys.platform

if plat.startswith('win'):
    plat = 'win'
elif plat.startswith('linux'):
    plat = 'linux'
elif plat.startswith('darwin') or plat.startswith('mac'):
    plat = 'osx'
else:
    assert 0, "Invalid platform: {}".format(sys.platform)

if platform.architecture()[0] == '32bit':
    assert 0, "Only 64-bit Blender is supported"

file = 'Taichi-Blend-{}-{}.zip'.format(plat, ver)
print('You should download', file)