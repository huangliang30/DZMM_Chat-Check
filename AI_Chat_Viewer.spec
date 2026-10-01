# -*- mode: python ; coding: utf-8 -*-
import importlib.util
import os

from PyInstaller.utils.hooks import collect_all

# tkinterdnd2 安装位置动态定位，本机与 CI 环境均可构建
_dnd_spec = importlib.util.find_spec("tkinterdnd2")
_dnd_dir = os.path.dirname(_dnd_spec.origin) if _dnd_spec else None

datas = [(_dnd_dir, 'tkinterdnd2')] if _dnd_dir else []
binaries = []
hiddenimports = ['tkinter', 'tkinterdnd2', 'tkinterdnd2.tkdnd', 'tkinter.ttk']
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
datas += [('good.ico', '.')]


a = Analysis(
    ['chat_viewer.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='AI_Chat_Check',
    icon='good.ico',
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
)
