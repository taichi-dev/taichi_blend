bundle:
	rm -rf build/Taichi-Blend
	mkdir -p build/Taichi-Blend
	python3 -m pip install --no-deps -r requirements.txt -t build/Taichi-Blend
	python3 -m pip install --no-deps dist/*.whl -t build/Taichi-Blend
	cp bundle.py build/Taichi-Blend/__init__.py
	cp -r taichi_blend build/Taichi-Blend
	rm -rf build/Taichi-Blend/include
	rm -rf build/Taichi-Blend/*.dist-info
	rm -rf build/Taichi-Blend/bin
	rm -f build/Taichi-Blend.zip
	cd build && zip -r Taichi-Blend.zip Taichi-Blend

.PHONY: bundle
