# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
	('sprite/*', 'sprite'),
    ('puzzles.json', '.'),
    ('tutorial.txt', '.'),
    ('about.txt', '.'),
    ('audio/music/*', 'audio/music'),
    ('audio/sfx/*', 'audio/sfx')
]


a = Analysis(
    ['dungeon_cross.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='dungeon_cross',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./sprite/book.png'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dungeon Cross',
)
app = BUNDLE(
    coll,
    name='Dungeon Cross.app',
    icon='./sprite/book.png',
    bundle_identifier=None,
)