del /f /s dist\*.whl
python setup.py bdist_wheel
mkdir build\Taichi-Blend
python -m pip install taichi_glsl dist\taichi_blend-0.0.1-py3-none-any.whl -t build\Taichi-Blend
copy bundle.py build\Taichi-Blend\__init__.py
del /f /s build\Taichi-Blend.zip
cd build
zip -r Taichi-Blend.zip Taichi-Blend
cd ..
