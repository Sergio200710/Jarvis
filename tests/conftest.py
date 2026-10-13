"""Fixtures comunes de las pruebas."""

from __future__ import annotations

import pytest

from jarvis.config import AppWhitelistItem, Config


@pytest.fixture
def config() -> Config:
    """Configuracion de prueba con lista blanca de apps."""
    return Config(
        carpetas_permitidas=["C:\\Temp"],
        apps_lista_blanca=[
            AppWhitelistItem(nombre="notepad", ruta="notepad.exe"),
            AppWhitelistItem(nombre="calculadora", ruta="calc.exe"),
        ],
    )
