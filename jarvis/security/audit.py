"""Registro de auditoria de las acciones de Jarvis (JSON Lines)."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jarvis.config import get_config_dir

if TYPE_CHECKING:
    from jarvis.tools.base import ToolSpec

_MAX_RESULTADO = 500


def resolve_audit_path(raw: str) -> Path:
    """Resuelve la ruta del log (relativa a la carpeta de configuracion)."""
    path = Path(raw)
    if not path.is_absolute():
        path = get_config_dir() / path
    return path


class AuditLog:
    """Escribe una linea JSON por cada accion ejecutada o rechazada."""

    def __init__(self, raw_path: str) -> None:
        self.path = resolve_audit_path(raw_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(
        self,
        request: str,
        spec: "ToolSpec",
        params: dict,
        result: str,
        estado: str = "ejecutado",
    ) -> None:
        """Anade una entrada de auditoria."""
        registro = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "peticion": request,
            "herramienta": spec.name,
            "riesgo": spec.risk,
            "parametros": _seguro(params),
            "estado": estado,
            "resultado": _recortar(result),
        }
        try:
            with self._lock, self.path.open("a", encoding="utf-8") as fichero:
                fichero.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except OSError:
            return


def _seguro(params: dict) -> dict:
    try:
        json.dumps(params, ensure_ascii=False)
        return params
    except (TypeError, ValueError):
        return {"_no_serializable": str(params)}


def _recortar(texto: str) -> str:
    texto = str(texto)
    if len(texto) <= _MAX_RESULTADO:
        return texto
    return texto[:_MAX_RESULTADO] + "..."
