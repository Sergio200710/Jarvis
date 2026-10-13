"""Arranque automatico con Windows mediante el registro (HKCU Run)."""

from __future__ import annotations

import logging
import sys
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Jarvis"


def command() -> str:
    """Comando que Windows ejecutara al iniciar sesion."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interprete = pythonw if pythonw.exists() else Path(sys.executable)
    script = Path(__file__).resolve().parents[2] / "main.py"
    return f'"{interprete}" "{script}"'


def is_enabled() -> bool:
    """True si Jarvis esta registrado para arrancar con Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        logger.warning("No pude consultar el arranque automatico")
        return False


def enable() -> None:
    """Registra Jarvis para arrancar con Windows."""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command())
    logger.info("Arranque automatico activado: %s", command())


def disable() -> None:
    """Quita a Jarvis del arranque con Windows."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        logger.info("Arranque automatico desactivado")
    except FileNotFoundError:
        return


def set_enabled(enabled: bool) -> None:
    """Activa o desactiva el arranque automatico."""
    if enabled:
        enable()
    else:
        disable()
