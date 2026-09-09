# -*- mode: python ; coding: utf-8 -*-

import customtkinter

block_cipher = None

a = Analysis(
    ['photo_organizer.py'],
    pathex=[],
    binaries=[],
    datas=[(os.path.dirname(customtkinter.__file__), 'customtkinter/')],
    hiddenimports=[
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'customtkinter',
        'organizer_core',
        'pillow_heif',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='photo_organizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='photo_organizer.icns'
)

# macOS specific bundle configuration
app = BUNDLE(
    exe,
    name='Photo Organizer.app',
    icon='photo_organizer.icns',
    bundle_identifier='se.express-it.photo-organizer',
    info_plist={
        'LSEnvironment': {
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
        },
        'CFBundleName': 'Photo Organizer',
        'CFBundleDisplayName': 'Photo Organizer',
        'CFBundleGetInfoString': 'Photo & Video Organization Tool',
        'CFBundleVersion': '2.1',
        'CFBundleShortVersionString': '2.1',
        'NSHighResolutionCapable': True,
    }
)