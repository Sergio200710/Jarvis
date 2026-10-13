"""Contrato que expone cada herramienta de Jarvis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

Riesgo = Literal["bajo", "medio", "alto"]


@dataclass(frozen=True)
class ToolSpec:
    """Descripcion y ejecutable de una habilidad."""

    name: str
    description: str
    parameters: dict
    risk: Riesgo
    handler: Callable[..., str]

    def to_schema(self) -> dict:
        """Esquema que se entrega al modelo para invocar la herramienta."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
