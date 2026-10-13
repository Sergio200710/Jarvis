"""Herramienta: abrir el navegador con una busqueda web."""

from __future__ import annotations

import logging
import webbrowser
from urllib.parse import quote_plus

from jarvis.tools.base import ToolSpec

logger = logging.getLogger(__name__)

_MOTOR = "https://www.google.com/search?q="


def run(**params: object) -> str:
    """Abre el navegador con la busqueda indicada (sin shell)."""
    consulta = str(params.get("consulta", "")).strip()
    if not consulta:
        return "No me has dicho qué buscar."
    url = _MOTOR + quote_plus(consulta)
    try:
        abierto = webbrowser.open(url, new=2)
    except Exception:  # noqa: BLE001 - se informa por voz
        logger.exception("Fallo al abrir el navegador")
        return "No he podido abrir el navegador."
    if not abierto:
        return "No he podido abrir el navegador."
    return f"He buscado '{consulta}' en el navegador."


SPEC = ToolSpec(
    name="buscar_web",
    description="Abre el navegador con una búsqueda en internet.",
    parameters={
        "type": "object",
        "properties": {
            "consulta": {
                "type": "string",
                "description": "Texto que se quiere buscar.",
            }
        },
        "required": ["consulta"],
    },
    risk="bajo",
    handler=run,
)
