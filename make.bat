@echo off
pip3 install -r requirements.txt
pip3 install -r requirements_to_build_windows_exe.txt
pip3 install pyinstaller
pyinstaller dungeon_cross.spec
