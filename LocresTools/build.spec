# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Locres CSV Tools  (onefile)
# Para compilar: pyinstaller build.spec

block_cipher = None

a = Analysis(
    ['Data\\locres_csv_importer.py'],
    pathex=['.'],
    hiddenimports=['pylocres', 'pypresence', 'PIL', 'PIL.Image', 'PIL.ImageTk'],
    binaries=[],
    datas=[
    ('Data\\banner.png',          'Data'),
    ('Data\\LocresToolsIcon.ico', 'Data'),
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LocresTools',
    icon='Data\\LocresToolsIcon.ico', 
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    runtime_tmpdir=None,   
)
