"""Contrato comun de las fuentes de entrada de ordenes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from jarvis.core.state import JarvisState


@dataclass(frozen=True)
class InputResult:
    """Orden obtenida del usuario (o su ausencia/cancelacion)."""

    text: str | None
    cancelled: bool
    had_input: bool


StateCallback = Callable[[JarvisState], None]


class InputProvider(Protocol):
    """Fuente de ordenes: ventana de texto o microfono."""

    def get_input(
        self, on_state: StateCallback, cancel: "object"
    ) -> InputResult:
        """Devuelve la orden del usuario, esperando lo necesario."""
        ...

    def shutdown(self) -> None:
        """Libera recursos de la fuente de entrada."""
        ...
