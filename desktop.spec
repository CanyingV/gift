# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：Windows 生成 exe，macOS 生成 app bundle（再打 dmg）。"""
import platform

is_mac = platform.system() == 'Darwin'

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=[('index.html', '.'), ('gift', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='礼单管家',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
)

if is_mac:
    app = BUNDLE(
        exe,
        name='礼单管家.app',
        icon=None,
        bundle_identifier='com.giftmanager.desktop',
    )
