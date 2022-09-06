all:
	make premake
	python3 -m PyInstaller dungeon_cross.spec
premake:
	make install-reqs
	pip3 install pyinstaller --user
install-reqs:
	pip3 install -r requirements.txt --user
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf __pycache__/
ve-build:
	pip3 install virtualenv --user
	virtualenv dungeon_cross_build
	. ./dungeon_cross_build/bin/activate
	make
	deactivate
ve-delete:
	rm -rf dungeon_cross_build
build-maps:
	python3 map_convert.py
