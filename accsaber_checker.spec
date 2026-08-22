# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller build spec for the AccSaber Ranking Checker.
# Works on both macOS (produces a .app bundle) and Windows (produces a folder
# containing the .exe). Build with:  pyinstaller accsaber_checker.spec --noconfirm
#
# Assumes this file lives at the repo root, alongside main.py, app.py,
# checker.py, and the libs/ folder.

block_cipher = None

# ---------------------------------------------------------------------------
# DATA FILES
# If checker.py or anything under libs/ reads non-code files (JSON criteria
# configs, lookup tables, etc.) using a path relative to its own location,
# list them here as (source, destination_folder_inside_bundle) tuples, e.g.:
#
#   datas = [
#       ('libs/criteria.json', 'libs'),
#       ('data', 'data'),
#   ]
#
# Leave it empty if your checker only reads the map folder the user selects
# at runtime (those paths are chosen live, so they don't need bundling).
# ---------------------------------------------------------------------------
datas = []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
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
    name='AccSaberRankingChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # GUI app: no terminal window. Set True temporarily to debug startup crashes.
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AccSaberRankingChecker',
)

# BUNDLE only does anything on macOS; it's ignored on Windows.
app = BUNDLE(
    coll,
    name='AccSaberRankingChecker.app',
    icon=None,
    bundle_identifier='com.accsaber.rankingchecker',
)
