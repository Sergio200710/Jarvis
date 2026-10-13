"""Herramienta: abrir una aplicacion de la lista blanca."""

from __future__ import annotations

import logging
import subprocess

from jarvis.tools.base import ToolSpec
from jarvis.tools.context import get_config

logger = logging.getLogger(__name__)


def _buscar_app(nombre: str):
    objetivo = nombre.strip().lower()
    for app in get_config().apps_lista_blanca:
        if app.nombre.lower() == objetivo:
            return app
    return None


def run(**params: object) -> str:
    """Abre un programa permitido sin usar shell y sin texto del modelo."""
    nombre = str(params.get("nombre", "")).strip()
    if not nombre:
        return "No me has dicho qué aplicación abrir."
    app = _buscar_app(nombre)
    if app is None:
        disponibles = ", ".join(a.nombre for a in get_config().apps_lista_blanca)
        return (
            f"No tengo registrada la aplicación '{nombre}'. "
            f"Puedo abrir: {disponibles}."
        )
    try:
        subprocess.Popen([app.ruta], shell=False, close_fds=True)
    except FileNotFoundError:
        logger.error("No se encontro el programa: %s", app.ruta)
        return f"No encuentro el programa de '{app.nombre}'."
    except OSError as exc:
        logger.error("Fallo al abrir %s: %s", app.ruta, exc)
        return f"No he podido abrir {app.nombre}."
    return f"He abierto {app.nombre}."


SPEC = ToolSpec(
    name="abrir_app",
    description="Abre una aplicación de la lista permitida.",
    parameters={
        "type": "object",
        "properties": {
            "nombre": {
                "type": "string",
                "description": "Nombre de la aplicación tal y como aparece en la lista permitida.",
            }
        },
        "required": ["nombre"],
    },
    risk="medio",
    handler=run,
)
