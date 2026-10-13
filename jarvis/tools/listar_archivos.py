"""Herramienta: listar el primer nivel de una carpeta permitida."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from jarvis.core.errors import SecurityError
from jarvis.tools.base import ToolSpec
from jarvis.tools.context import get_config
from jarvis.security.paths import ensure_allowed

logger = logging.getLogger(__name__)

MAX_ENTRADAS = 50


def _tamano_legible(num: float) -> str:
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024 or unidad == "TB":
            return f"{num:.0f} {unidad}" if unidad == "B" else f"{num:.1f} {unidad}"
        num /= 1024
    return f"{num:.1f} TB"


def run(**params: object) -> str:
    """Lista nombre, tipo, tamano y fecha del primer nivel de la carpeta."""
    ruta = str(params.get("ruta", "")).strip()
    if not ruta:
        return "No me has dicho qué carpeta listar."

    try:
        base = ensure_allowed(ruta, get_config().carpetas_permitidas)
    except SecurityError as exc:
        return str(exc)

    if not base.exists() or not base.is_dir():
        return f"No encuentro la carpeta '{ruta}'."

    entradas = sorted(base.iterdir(), key=lambda p: p.name.lower())[:MAX_ENTRADAS]
    if not entradas:
        return f"La carpeta '{base.name}' está vacía."

    lineas = [f"Contenido de {base}:"]
    for item in entradas:
        try:
            datos = item.stat()
            fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            logger.warning("No pude leer datos de %s", item)
            fecha = "desconocida"
        if item.is_dir():
            lineas.append(f"- carpeta '{item.name}' (mod {fecha})")
        else:
            tamano = _tamano_legible(datos.st_size) if datos else "?"
            lineas.append(f"- archivo '{item.name}' ({tamano}, mod {fecha})")

    if len(entradas) == MAX_ENTRADAS:
        lineas.append(f"(mostrando las primeras {MAX_ENTRADAS} entradas)")
    return "\n".join(lineas)


SPEC = ToolSpec(
    name="listar_archivos",
    description="Lista el contenido del primer nivel de una carpeta permitida.",
    parameters={
        "type": "object",
        "properties": {
            "ruta": {
                "type": "string",
                "description": "Ruta de la carpeta a listar (dentro de las permitidas).",
            }
        },
        "required": ["ruta"],
    },
    risk="bajo",
    handler=run,
)
