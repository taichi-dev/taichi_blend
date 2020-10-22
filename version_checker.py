import sys
import platform
major = sys.version_info.major
minor = sys.version_info.minor
assert major == 3 and minor in [6, 7, 8], "Only Python 3.6/3.7/3.8 is supported"

ver = str(major) + str(minor)

if sys.platform.lower().startswith('win'):
    plat = 'win'
elif sys.platform.lower().startswith('linux'):
    plat = 'linux'
else:
    assert 0, "Invalid platform: {}".format(sys.platform)

file = 'Taichi-Blend-{}-{}.zip'.format(plat, ver)
print('You should download', file)