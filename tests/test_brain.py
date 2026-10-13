"""Pruebas del bucle de tool calling con un proveedor falso."""

from __future__ import annotations

import pytest

from jarvis.brain.agent import Brain
from jarvis.brain.client import create_client
from jarvis.brain.providers import Reply, ToolCall
from jarvis.config import Config
from jarvis.core.errors import BrainError
from jarvis.security.permissions import SecurityManager
from jarvis.tools.base import ToolSpec
from jarvis.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self, replies) -> None:
        self._replies = list(replies)
        self.messages: list | None = None
        self.systems: list[str] = []

    def new_messages(self, user_text: str) -> list:
        self.messages = [{"role": "user", "content": user_text}]
        return self.messages

    def complete(self, messages: list, system: str) -> Reply:
        self.systems.append(system)
        return self._replies.pop(0)

    def append_assistant(self, messages: list, reply: Reply) -> None:
        messages.append({"role": "assistant", "content": reply.raw})

    def append_tool_results(self, messages: list, results) -> None:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": cid, "content": content}
                    for cid, content in results
                ],
            }
        )


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
    provider = FakeProvider(
        [
            Reply(text="", tool_calls=[ToolCall("tu1", "eco", {})], raw="assistant-1"),
            Reply(text="Ya está."),
        ]
    )
    brain = Brain(config, _registry(), provider=provider)

    assert brain.respond("hazlo") == "Ya está."
    ultimo = provider.messages[-1]
    assert ultimo["content"][0]["type"] == "tool_result"
    assert ultimo["content"][0]["content"] == "resultado-tool"


def test_respond_sin_herramientas(config: Config) -> None:
    provider = FakeProvider([Reply(text="Hola.")])
    brain = Brain(config, _registry(), provider=provider)
    assert brain.respond("hola") == "Hola."


def test_herramienta_desconocida_no_rompe(config: Config) -> None:
    provider = FakeProvider(
        [
            Reply(text="", tool_calls=[ToolCall("tu1", "noexiste", {})]),
            Reply(text="Vale."),
        ]
    )
    brain = Brain(config, _registry(), provider=provider)
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
    provider = FakeProvider(
        [
            Reply(text="", tool_calls=[ToolCall("tu1", "peligrosa", {})]),
            Reply(text="Vale."),
        ]
    )
    security = SecurityManager(config, dialog=_DialogFalse(), audit=None)
    brain = Brain(config, registry, provider=provider, security=security)

    resultado = brain.respond("borra todo")

    assert resultado == "Vale."
    assert llamado == []
    tool_result = provider.messages[-1]["content"][0]
    assert "lo dejo" in tool_result["content"].lower()
