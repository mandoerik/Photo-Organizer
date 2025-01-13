# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['photo_organizer.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
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
    icon=['photo_organizer.icns'],
)
app = BUNDLE(
    exe,
    name='photo_organizer.app',
    icon='photo_organizer.icns',
    bundle_identifier='com.express-it.photoorganizer',
    info_plist={
        'CFBundleName': 'Photo Organizer',
        'CFBundleDisplayName': 'Photo Organizer',
        'CFBundleGetInfoString': "Photo & Video Organizer",
        'CFBundleVersion': "1.2",
        'CFBundleShortVersionString': "1.2",
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
        'NSRequiresAquaSystemAppearance': False,
        'LSEnvironment': {
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
        }
    },
)