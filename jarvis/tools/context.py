"""Acceso de las herramientas a la configuracion en tiempo de ejecucion."""

from __future__ import annotations

from jarvis.config import Config
from jarvis.core.errors import ConfigError

_config: Config | None = None


def set_config(config: Config) -> None:
    """Guarda la configuracion activa para que las herramientas la consulten."""
    global _config
    _config = config


def get_config() -> Config:
    """Devuelve la configuracion activa."""
    if _config is None:
        raise ConfigError("No hay configuracion cargada para las herramientas.")
    return _config
