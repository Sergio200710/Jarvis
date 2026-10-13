"""Atajo global de teclado para activar Jarvis."""

from __future__ import annotations

import logging
from collections.abc import Callable

import keyboard

logger = logging.getLogger(__name__)


class HotkeyListener:
    """Registra y libera un atajo global."""

    def __init__(self, combo: str, on_trigger: Callable[[], None]) -> None:
        self._combo = combo
        self._on_trigger = on_trigger
        self._handle: object | None = None

    def start(self) -> None:
        """Activa el atajo global."""
        if self._handle is not None:
            return
        self._handle = keyboard.add_hotkey(self._combo, self._on_trigger)
        logger.info("Atajo global registrado: %s", self._combo)

    def stop(self) -> None:
        """Libera el atajo global si estaba activo."""
        if self._handle is None:
            return
        try:
            keyboard.remove_hotkey(self._handle)
        except (KeyError, ValueError):
            logger.warning("No se pudo liberar el atajo %s", self._combo)
        finally:
            self._handle = None
            logger.info("Atajo global liberado")
