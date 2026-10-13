"""Pruebas de los proveedores del modelo (formato OpenAI/Groq)."""

from __future__ import annotations

import pytest

from jarvis.brain.providers import (
    AnthropicProvider,
    GroqProvider,
    Reply,
    ToolCall,
    build_provider,
)
from jarvis.config import Config
from jarvis.core.errors import BrainError
from jarvis.tools.base import ToolSpec


class FakeResponse:
    def __init__(self, data) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self._data


class FakeHttp:
    def __init__(self, data) -> None:
        self.data = data
        self.calls: list[dict] = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append(
            {"url": url, "json": json, "headers": headers, "timeout": timeout}
        )
        return FakeResponse(self.data)


def _tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="eco",
            description="devuelve eco",
            parameters={"type": "object", "properties": {}, "required": []},
            risk="bajo",
            handler=lambda **kwargs: "ok",
        )
    ]


def _data(message: dict) -> dict:
    return {"choices": [{"message": message}]}


def test_groq_tool_schema(config: Config) -> None:
    provider = GroqProvider(config, _tools())
    schema = provider._tool_schemas()[0]
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "eco"
    assert schema["function"]["parameters"] == _tools()[0].parameters


def test_groq_complete_parsea_texto_y_tools(config: Config, monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "clave-test")
    http = FakeHttp(
        _data(
            {
                "content": "Pensando.",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "eco", "arguments": '{"x": 1}'},
                    }
                ],
            }
        )
    )
    provider = GroqProvider(config, _tools(), http_client=http)

    reply = provider.complete([{"role": "user", "content": "hola"}], "eres jarvis")

    assert reply.text == "Pensando."
    assert reply.tool_calls == [ToolCall("call_1", "eco", {"x": 1})]
    enviado = http.calls[0]
    assert enviado["url"].endswith("/chat/completions")
    assert enviado["json"]["messages"][0] == {"role": "system", "content": "eres jarvis"}
    assert enviado["headers"]["Authorization"] == "Bearer clave-test"


def test_groq_sin_clave(config: Config, monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider = GroqProvider(config, _tools(), http_client=FakeHttp(_data({"content": "x"})))
    with pytest.raises(BrainError):
        provider.complete([{"role": "user", "content": "hola"}], "sys")


def test_groq_append_mensajes(config: Config) -> None:
    provider = GroqProvider(config, _tools(), http_client=FakeHttp(_data({"content": "x"})))
    messages: list = provider.new_messages("hola")
    reply = Reply(text="ok", raw={"role": "assistant", "content": None}, tool_calls=[])
    reply.raw["tool_calls"] = [{"id": "call_1"}]
    provider.append_assistant(messages, reply)
    provider.append_tool_results(messages, [("call_1", "resultado")])

    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"] == [{"id": "call_1"}]
    assert messages[2] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "resultado",
    }


def test_build_provider(config: Config) -> None:
    assert isinstance(build_provider(config, _tools()), GroqProvider)
    config.modelo.proveedor = "anthropic"
    assert isinstance(build_provider(config, _tools()), AnthropicProvider)
