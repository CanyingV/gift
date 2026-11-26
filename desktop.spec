# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：Windows 生成 exe，macOS 生成 app bundle（再打 dmg）。"""
import platform
import os

is_mac = platform.system() == 'Darwin'
# 图标文件：优先按 spec 所在目录定位，若 __file__ 不可用则回退到当前工作目录
try:
    _base = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _base = os.getcwd()
ICON_DIR = os.path.join(_base, 'app_icons')
ICO = os.path.join(ICON_DIR, 'icon.ico')
ICNS = os.path.join(ICON_DIR, 'icon.icns')

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    # 前端页面按模块拆到了 templates/ 与 static/；后端包 server/ 由 import 自动收集
    datas=[('templates', 'templates'), ('static', 'static'), ('gift', '.')],
    hiddenimports=['peewee', 'server', 'server.config', 'server.models', 'server.repository',
                   'server.xlsx', 'server.importer', 'server.exporter', 'server.routes',
                   'server.handler'],
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
    name='礼记',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=ICNS if is_mac else ICO,
)

if is_mac:
    app = BUNDLE(
        exe,
        name='礼记.app',
        icon=ICNS,
        bundle_identifier='com.giftmanager.desktop',
    )
