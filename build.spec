# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 核心路径锁定
cwd = os.getcwd()
venv_path = os.path.join(cwd, '.venv')
site_packages = os.path.join(venv_path, 'Lib', 'site-packages')

# 显式寻找 PyQt6 的 DLL 目录（针对 3.13 特别加固）
pyqt6_dir = os.path.join(site_packages, 'PyQt6')
qt_bin_dir = os.path.join(pyqt6_dir, 'Qt6', 'bin')

# 1. 收集资源
qf_datas = collect_data_files('qfluentwidgets') if os.path.exists(os.path.join(site_packages, 'qfluentwidgets')) else []

a = Analysis(
    ['main.py'],
    pathex=[cwd], # 移除 site_packages 的直接注入，避免 PyInstaller 警告
    binaries=[],
    datas=[
        ('bin', 'bin'),
        ('bd_toolbox.ico', '.'),
    ] + qf_datas,
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
    icon=['bd_toolbox.ico'],
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
