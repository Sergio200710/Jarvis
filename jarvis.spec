# -*- mode: python ; coding: utf-8 -*-
"""Configuracion de PyInstaller para Jarvis (onedir, sin consola)."""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

_paquetes = [
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "tokenizers",
    "av",
    "huggingface_hub",
    "anthropic",
    "httpcore2",
    "httpx2",
    "comtypes",
    "pyttsx3",
    "pystray",
    "PIL",
    "keyboard",
    "sounddevice",
]

for _pkg in _paquetes:
    try:
        _d, _b, _h = collect_all(_pkg)
    except Exception:
        continue
    datas += _d
    binaries += _b
    hiddenimports += _h

hiddenimports += ["tkinter", "tkinter.filedialog", "tkinter.simpledialog"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "matplotlib", "pytest", "IPython"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Jarvis",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Jarvis",
)
