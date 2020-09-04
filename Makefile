bundle: package
	mkdir -p build/Taichi-Blend
	python3 -m pip install dist/*.whl -t build/Taichi-Blend
	cp bundle.py build/Taichi-Blend/__init__.py
	rm -f build/Taichi-Blend.zip
	cd build && zip -r Taichi-Blend.zip Taichi-Blend

package:
	rm -rf dist/*
	python3 setup.py bdist_wheel

.PHONY: bundle
