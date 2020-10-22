PYPLATFORM=${1?Specify the target platform: win, linux, osx}
PYVERSION=${2?Specify the Blender Python version: 36, 37, 38}
case $PYPLATFORM in
linux) PIPPLAT=manylinux1_x86_64;;
win) PIPPLAT=win_amd64;;
osx) PIPPLAT=macosx_10_14_x86_64;;
esac
 

rm -rf build/Taichi-Blend
mkdir -p build
cp -r src build/Taichi-Blend
mkdir -p build/Taichi-Blend/bundle-packages
pip install --python-version $PYVERSION --platform $PIPPLAT --no-deps -r requirements.txt -t build/Taichi-Blend/bundle-packages
rm -rf build/Taichi-Blend/bundle-packages/include
rm -rf build/Taichi-Blend/bundle-packages/*.dist-info
rm -rf build/Taichi-Blend/bundle-packages/*.egg-info
rm -rf build/Taichi-Blend/bundle-packages/__pycache__
rm -rf build/Taichi-Blend/bundle-packages/*/__pycache__
rm -rf build/Taichi-Blend/bundle-packages/*/*/__pycache__
rm -rf build/Taichi-Blend/bundle-packages/bin
rm -f build/Taichi-Blend.zip
cd build
rm -rf Taichi-Blend-$PYPLATFORM-$PYVERSION.zip
zip -r Taichi-Blend-$PYPLATFORM-$PYVERSION.zip Taichi-Blend
