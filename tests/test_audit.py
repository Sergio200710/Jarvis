"""Pruebas del log de auditoria."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis.security.audit import AuditLog, resolve_audit_path
from jarvis.tools.base import ToolSpec


def _spec() -> ToolSpec:
    return ToolSpec(
        name="t",
        description="descripcion",
        parameters={"type": "object", "properties": {}},
        risk="alto",
        handler=lambda **kwargs: "x",
    )


def test_audit_escribe_json(tmp_path: Path) -> None:
    path = tmp_path / "audit.log"
    AuditLog(str(path)).log("hola", _spec(), {"a": 1}, "resultado", "ejecutado")

    lineas = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lineas) == 1
    registro = json.loads(lineas[0])
    assert registro["peticion"] == "hola"
    assert registro["herramienta"] == "t"
    assert registro["riesgo"] == "alto"
    assert registro["parametros"] == {"a": 1}
    assert registro["estado"] == "ejecutado"
    assert registro["resultado"] == "resultado"
    assert "fecha" in registro


def test_audit_anade_lineas(tmp_path: Path) -> None:
    path = tmp_path / "a.log"
    log = AuditLog(str(path))
    log.log("uno", _spec(), {}, "r")
    log.log("dos", _spec(), {}, "r")
    assert len(path.read_text(encoding="utf-8").strip().splitlines()) == 2


def test_audit_recorta_resultado_largo(tmp_path: Path) -> None:
    path = tmp_path / "a.log"
    AuditLog(str(path)).log("x", _spec(), {}, "y" * 1000)
    registro = json.loads(path.read_text(encoding="utf-8").strip())
    assert registro["resultado"].endswith("...")
    assert len(registro["resultado"]) <= 503


def test_audit_parametros_no_serializables(tmp_path: Path) -> None:
    path = tmp_path / "a.log"
    AuditLog(str(path)).log("x", _spec(), {"s": {1, 2}}, "r")
    registro = json.loads(path.read_text(encoding="utf-8").strip())
    assert "_no_serializable" in registro["parametros"]


def test_resolve_audit_path_relativo() -> None:
    path = resolve_audit_path("logs/audit.log")
    assert path.is_absolute()
    assert path.name == "audit.log"
