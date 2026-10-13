"""Icono y menu de Jarvis en la bandeja del sistema."""

from __future__ import annotations

import logging

import pystray
from PIL import Image, ImageDraw

from jarvis.core.orchestrator import Orchestrator
from jarvis.utils.autostart import is_enabled, set_enabled

logger = logging.getLogger(__name__)

_ICON_SIZE = 64


def _build_image() -> Image.Image:
    """Genera el icono de la bandeja embebido (sin archivos externos)."""
    image = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, _ICON_SIZE - 4, _ICON_SIZE - 4), fill=(30, 90, 200, 255))
    draw.text((22, 18), "J", fill=(255, 255, 255, 255))
    return image


class TrayActivator:
    """Bandeja con menu Activar/Salir."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        self._orchestrator = orchestrator
        self._icon = pystray.Icon(
            name="Jarvis",
            icon=_build_image(),
            title="Jarvis",
            menu=pystray.Menu(
                pystray.MenuItem("Activar", self._on_activate, default=True),
                pystray.MenuItem(
                    "Iniciar con Windows",
                    self._on_toggle_autostart,
                    checked=lambda item: is_enabled(),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self._on_exit),
            ),
        )

    def _on_activate(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._orchestrator.toggle()

    def _on_toggle_autostart(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        set_enabled(not is_enabled())

    def _on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        logger.info("Salida solicitada desde la bandeja")
        self._orchestrator.stop()

    def run(self) -> None:
        """Ejecuta el bucle de la bandeja (bloquea el hilo actual)."""
        logger.info("Bandeja del sistema iniciada")
        self._icon.run()

    def stop(self) -> None:
        """Detiene la bandeja."""
        self._icon.stop()
