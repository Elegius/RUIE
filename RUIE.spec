# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for RUIE (RSI Launcher UI Editor)
# NOTE: Uses directory-based distribution (not --onefile) to avoid DLL extraction issues
# with paths containing spaces. Ensure the entire RUIE folder is kept together.

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('public', 'public'),
        ('assets', 'assets'),
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'PyQt5',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebChannel',
        'server',
        'launcher_detector',
        'color_replacer',
        'media_replacer',
        'waitress',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'itsdangerous',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='RUIE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RUIE',
)
