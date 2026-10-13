"""Estados internos de Jarvis y eventos que los provocan."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class JarvisState(Enum):
    """Estado de la maquina del orquestador."""

    IDLE = auto()
    LISTENING = auto()
    TRANSCRIBING = auto()
    THINKING = auto()
    CONFIRMING = auto()
    SPEAKING = auto()


class EventKind(Enum):
    """Tipos de evento aceptados por el orquestador."""

    ACTIVATE = auto()
    CANCEL = auto()
    SHUTDOWN = auto()


@dataclass(frozen=True)
class Event:
    """Evento encolado hacia el orquestador."""

    kind: EventKind
    payload: dict[str, Any] = field(default_factory=dict)
