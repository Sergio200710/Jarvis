"""Herramienta: hora y fecha actuales."""

from __future__ import annotations

from datetime import datetime

from jarvis.tools.base import ToolSpec

_DIAS = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]
_MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def run(**params: object) -> str:
    """Devuelve la fecha y hora actuales en texto natural."""
    ahora = datetime.now()
    dia = _DIAS[ahora.weekday()]
    mes = _MESES[ahora.month - 1]
    return (
        f"Hoy es {dia} {ahora.day} de {mes} de {ahora.year} "
        f"y son las {ahora.hour:02d}:{ahora.minute:02d}."
    )


SPEC = ToolSpec(
    name="hora_y_fecha",
    description="Devuelve la fecha y la hora actuales del sistema.",
    parameters={"type": "object", "properties": {}, "required": []},
    risk="bajo",
    handler=run,
)
