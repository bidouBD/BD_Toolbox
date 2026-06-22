# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import sysconfig
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 核心路径锁定
cwd = os.getcwd()
site_packages = sysconfig.get_paths()["purelib"]

# 1. 收集资源
qf_datas = collect_data_files('qfluentwidgets') if os.path.exists(os.path.join(site_packages, 'qfluentwidgets')) else []
datas = []
if os.path.exists('bin'):
    datas.append(('bin', 'bin'))
for icon_candidate in ('bd_toolbox.ico', 'bd_toolbox.icns', 'bd_toolbox.png'):
    if os.path.exists(icon_candidate):
        datas.append((icon_candidate, '.'))

# Icon setting
icon_file = 'bd_toolbox.ico'
if sys.platform == 'darwin':
    if os.path.exists('bd_toolbox.icns'):
        icon_file = 'bd_toolbox.icns'
    elif os.path.exists('bd_toolbox.png'):
        icon_file = 'bd_toolbox.png'

a = Analysis(
    ['main.py'],
    pathex=[cwd],
    binaries=[],
    datas=datas + qf_datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'qfluentwidgets',
        'darkdetect',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 显式拦截庞大库
    excludes=['PyQt5', 'PySide6', 'flet', 'customtkinter', 'torch', 'transformers', 'pandas', 'numpy', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 2. 强制二进制过滤：杀掉所有 Qt5/PySide 残留，并确保 PyQt6 的 DLL 存在
a.binaries = [x for x in a.binaries if not any(err in x[0].lower() for err in ['qt5', 'pyside'])]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BD_Toolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    icon=[icon_file] if icon_file else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BD_Toolbox',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='BD_Toolbox.app',
        icon=icon_file if icon_file.endswith('.icns') else None,
        bundle_identifier='com.bidou.bdtoolbox',
    )
