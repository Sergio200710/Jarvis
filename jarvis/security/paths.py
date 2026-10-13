"""Validacion de rutas contra las carpetas permitidas."""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.core.errors import SecurityError


def _norm(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def is_within(candidate: Path, root: Path) -> bool:
    """True si candidate queda dentro de root (o es root), tras resolver '..'."""
    child = _norm(candidate)
    parent = _norm(root)
    try:
        comun = os.path.commonpath([child, parent])
    except ValueError:
        return False
    return comun == parent


def ensure_allowed(raw: str, allowed: list[str]) -> Path:
    """Resuelve y valida una ruta, lanzando SecurityError si queda fuera."""
    if not raw or not raw.strip():
        raise SecurityError("No me has indicado ninguna ruta.")
    if not allowed:
        raise SecurityError("No hay carpetas permitidas configuradas.")

    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = Path(allowed[0]).expanduser() / candidate
    resolved = candidate.resolve()

    for root in allowed:
        if is_within(resolved, Path(root).expanduser()):
            return resolved

    raise SecurityError(
        f"La ruta '{raw}' está fuera de las carpetas permitidas."
    )
