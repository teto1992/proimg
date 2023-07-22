install: build
	pip3 install dist/*.whl --force-reinstall

uninstall:
	pip3 uninstall proimg -y

build: clean
	python3 -m build

clean:
	rm -rf dist

