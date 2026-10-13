"""Pruebas del registro de herramientas."""

from __future__ import annotations

import pytest

from jarvis.tools.base import ToolSpec
from jarvis.tools.registry import ToolRegistry, discover


def _spec(name: str) -> ToolSpec:
    return ToolSpec(
        name=name,
        description="descripcion",
        parameters={"type": "object", "properties": {}},
        risk="bajo",
        handler=lambda **kwargs: "ok",
    )


def test_registrar_y_obtener() -> None:
    registry = ToolRegistry()
    spec = _spec("uno")
    registry.register(spec)
    assert registry.get("uno") is spec
    assert registry.names() == ["uno"]
    assert registry.get("otro") is None


def test_nombre_duplicado_falla() -> None:
    registry = ToolRegistry()
    registry.register(_spec("uno"))
    with pytest.raises(ValueError):
        registry.register(_spec("uno"))


def test_schemas_para_el_modelo() -> None:
    registry = ToolRegistry()
    registry.register(_spec("uno"))
    assert registry.schemas() == [
        {
            "name": "uno",
            "description": "descripcion",
            "input_schema": {"type": "object", "properties": {}},
        }
    ]


def test_discover_encuentra_todas_las_herramientas() -> None:
    registry = discover()
    nombres = set(registry.names())
    assert {"hora_y_fecha", "abrir_app", "buscar_web", "listar_archivos"} <= nombres
    assert nombres.isdisjoint({"base", "registry", "context", "__init__"})


def test_discover_schemas_validos() -> None:
    for schema in discover().schemas():
        assert schema["name"]
        assert schema["input_schema"]["type"] == "object"
