PYVERSION=${1?Specify the Blender Python version, e.g. 37}

rm -rf build/Taichi-Blend
mkdir -p build/Taichi-Blend/bundle-packages
cp -r src build/Taichi-Blend
pip install --python-version $PYVERSION --no-deps -r requirements.txt -t build/Taichi-Blend/bundle-packages
rm -rf build/Taichi-Blend/bundle-packages/include
rm -rf build/Taichi-Blend/bundle-packages/*.dist-info
rm -rf build/Taichi-Blend/bundle-packages/*.egg-info
rm -rf build/Taichi-Blend/bundle-packages/__pycache__
rm -rf build/Taichi-Blend/bundle-packages/*/__pycache__
rm -rf build/Taichi-Blend/bin
rm -f build/Taichi-Blend.zip
cd build && zip -r Taichi-Blend.zip Taichi-Blend
