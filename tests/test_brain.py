"""Pruebas del bucle de tool calling con un cliente falso."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from jarvis.brain.agent import Brain
from jarvis.brain.client import create_client
from jarvis.config import Config
from jarvis.core.errors import BrainError
from jarvis.security.permissions import SecurityManager
from jarvis.tools.base import ToolSpec
from jarvis.tools.registry import ToolRegistry


class FakeMessages:
    def __init__(self, responses) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses) -> None:
        self.messages = FakeMessages(responses)


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="eco",
            description="devuelve eco",
            parameters={"type": "object", "properties": {}, "required": []},
            risk="bajo",
            handler=lambda **kwargs: "resultado-tool",
        )
    )
    return registry


def test_respond_ejecuta_herramienta(config: Config) -> None:
    tool_use = SimpleNamespace(type="tool_use", id="tu1", name="eco", input={})
    primera = SimpleNamespace(content=[tool_use])
    segunda = SimpleNamespace(content=[SimpleNamespace(type="text", text="Ya está.")])
    client = FakeClient([primera, segunda])
    brain = Brain(config, _registry(), client=client)

    assert brain.respond("hazlo") == "Ya está."
    ultimo = client.messages.calls[1]["messages"][-1]
    assert ultimo["content"][0]["type"] == "tool_result"
    assert ultimo["content"][0]["content"] == "resultado-tool"


def test_respond_sin_herramientas(config: Config) -> None:
    respuesta = SimpleNamespace(content=[SimpleNamespace(type="text", text="Hola.")])
    brain = Brain(config, _registry(), client=FakeClient([respuesta]))
    assert brain.respond("hola") == "Hola."


def test_herramienta_desconocida_no_rompe(config: Config) -> None:
    tool_use = SimpleNamespace(type="tool_use", id="tu1", name="noexiste", input={})
    primera = SimpleNamespace(content=[tool_use])
    segunda = SimpleNamespace(content=[SimpleNamespace(type="text", text="Vale.")])
    brain = Brain(config, _registry(), client=FakeClient([primera, segunda]))
    assert brain.respond("hazlo") == "Vale."


def test_create_client_sin_clave(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(BrainError):
        create_client(30)


class _DialogFalse:
    def ask_yes_no(self, question: str) -> bool:
        return False


def test_brain_respeta_la_confirmacion(config: Config) -> None:
    registry = ToolRegistry()
    llamado: list[int] = []
    registry.register(
        ToolSpec(
            name="peligrosa",
            description="descripcion",
            parameters={"type": "object", "properties": {}, "required": []},
            risk="alto",
            handler=lambda **kwargs: llamado.append(1) or "hecho",
        )
    )
    tool_use = SimpleNamespace(type="tool_use", id="tu1", name="peligrosa", input={})
    primera = SimpleNamespace(content=[tool_use])
    segunda = SimpleNamespace(content=[SimpleNamespace(type="text", text="Vale.")])
    client = FakeClient([primera, segunda])
    security = SecurityManager(config, dialog=_DialogFalse(), audit=None)
    brain = Brain(config, registry, client=client, security=security)

    resultado = brain.respond("borra todo")

    assert resultado == "Vale."
    assert llamado == []
    tool_result = client.messages.calls[1]["messages"][-1]["content"][0]
    assert "lo dejo" in tool_result["content"].lower()
