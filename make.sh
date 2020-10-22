PYVERSION=${1?Specify the Blender Python version, e.g. 37}

rm -rf build/Taichi-Blend
mkdir -p build/Taichi-Blend
pip install --python-version $PYVERSION --no-deps -r requirements.txt -t build/Taichi-Blend
cp bundle.py build/Taichi-Blend/__init__.py
cp -r numblend build/Taichi-Blend
rm -rf build/Taichi-Blend/include
rm -rf build/Taichi-Blend/*.dist-info
rm -rf build/Taichi-Blend/*.egg-info
rm -rf build/Taichi-Blend/__pycache__
rm -rf build/Taichi-Blend/bin
rm -f build/Taichi-Blend.zip
cd build && zip -r Taichi-Blend.zip Taichi-Blend
