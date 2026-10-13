"""Proveedores del modelo: Anthropic y compatibles con OpenAI (Groq).

El bucle de tool calling (`agent.py`) es agnostico al proveedor: cada uno traduce
los mensajes y las herramientas a su formato nativo.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from jarvis.config import Config
from jarvis.core.errors import BrainError
from jarvis.tools.base import ToolSpec

logger = logging.getLogger(__name__)

MAX_TOKENS = 1024

_API_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
}

_BASE_URL = {
    "groq": "https://api.groq.com/openai/v1",
}


@dataclass
class ToolCall:
    """Una herramienta que el modelo pide ejecutar."""

    id: str
    name: str
    arguments: dict


@dataclass
class Reply:
    """Respuesta normalizada del modelo."""

    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None


class Provider(ABC):
    """Traduce el bucle de herramientas al formato de cada proveedor."""

    def __init__(self, config: Config, tools: list[ToolSpec]) -> None:
        self._config = config
        self._tools = tools
        self._max_tokens = MAX_TOKENS

    @abstractmethod
    def new_messages(self, user_text: str) -> list: ...

    @abstractmethod
    def complete(self, messages: list, system: str) -> Reply: ...

    @abstractmethod
    def append_assistant(self, messages: list, reply: Reply) -> None: ...

    @abstractmethod
    def append_tool_results(
        self, messages: list, results: list[tuple[str, str]]
    ) -> None: ...

    @abstractmethod
    def _tool_schemas(self) -> list: ...


class AnthropicProvider(Provider):
    """Proveedor para el SDK de Anthropic (Claude)."""

    def __init__(self, config: Config, tools: list[ToolSpec], client=None) -> None:
        super().__init__(config, tools)
        self._client = client

    def _ensure_client(self):
        if self._client is None:
            from jarvis.brain.client import create_client

            env = self._config.modelo.api_key_env or _API_KEY_ENV["anthropic"]
            self._client = create_client(
                self._config.modelo.timeout_segundos, api_key_env=env
            )
        return self._client

    def _tool_schemas(self) -> list:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in self._tools
        ]

    def new_messages(self, user_text: str) -> list:
        return [{"role": "user", "content": user_text}]

    def complete(self, messages: list, system: str) -> Reply:
        client = self._ensure_client()
        try:
            response = client.messages.create(
                model=self._config.modelo.nombre,
                max_tokens=self._max_tokens,
                system=system,
                messages=messages,
                tools=self._tool_schemas(),
            )
        except Exception as exc:  # noqa: BLE001 - se informa por voz
            logger.error("Fallo al llamar al modelo: %s", exc)
            raise BrainError("No he podido contactar con el modelo.") from exc

        texts: list[str] = []
        calls: list[ToolCall] = []
        for block in response.content:
            kind = getattr(block, "type", None)
            if kind == "text":
                texts.append(block.text)
            elif kind == "tool_use":
                calls.append(
                    ToolCall(block.id, block.name, dict(block.input or {}))
                )
        text = " ".join(t.strip() for t in texts if t).strip()
        return Reply(text=text, tool_calls=calls, raw=response.content)

    def append_assistant(self, messages: list, reply: Reply) -> None:
        messages.append({"role": "assistant", "content": reply.raw})

    def append_tool_results(
        self, messages: list, results: list[tuple[str, str]]
    ) -> None:
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": content,
                    }
                    for call_id, content in results
                ],
            }
        )


class GroqProvider(Provider):
    """Proveedor para endpoints compatibles con la API de OpenAI (Groq)."""

    def __init__(self, config: Config, tools: list[ToolSpec], http_client=None) -> None:
        super().__init__(config, tools)
        self._http = http_client

    def _ensure_http(self):
        if self._http is None:
            import httpx2

            self._http = httpx2.Client()
        return self._http

    def _api_key(self) -> str:
        env = self._config.modelo.api_key_env or _API_KEY_ENV["groq"]
        key = os.environ.get(env)
        if not key:
            raise BrainError(
                f"Falta la variable de entorno {env}. "
                "Configúrala para que pueda pensar."
            )
        return key

    def _url(self) -> str:
        base = self._config.modelo.base_url or _BASE_URL["groq"]
        return base.rstrip("/") + "/chat/completions"

    def _tool_schemas(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools
        ]

    def new_messages(self, user_text: str) -> list:
        return [{"role": "user", "content": user_text}]

    def complete(self, messages: list, system: str) -> Reply:
        payload = {
            "model": self._config.modelo.nombre,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": self._tool_schemas(),
            "tool_choice": "auto",
        }
        headers = {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
        }
        try:
            response = self._ensure_http().post(
                self._url(),
                json=payload,
                headers=headers,
                timeout=self._config.modelo.timeout_segundos,
            )
            response.raise_for_status()
            data = response.json()
        except BrainError:
            raise
        except Exception as exc:  # noqa: BLE001 - se informa por voz
            logger.error("Fallo al llamar al modelo: %s", exc)
            raise BrainError("No he podido contactar con el modelo.") from exc

        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Respuesta inesperada del modelo: %s", data)
            raise BrainError("El modelo ha devuelto una respuesta inesperada.") from exc

        text = (message.get("content") or "").strip()
        calls: list[ToolCall] = []
        for raw_call in message.get("tool_calls") or []:
            function = raw_call.get("function", {})
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            calls.append(
                ToolCall(raw_call.get("id", ""), function.get("name", ""), arguments)
            )
        return Reply(text=text, tool_calls=calls, raw=message)

    def append_assistant(self, messages: list, reply: Reply) -> None:
        message = {"role": "assistant", "content": reply.raw.get("content")}
        if reply.raw.get("tool_calls"):
            message["tool_calls"] = reply.raw["tool_calls"]
        messages.append(message)

    def append_tool_results(
        self, messages: list, results: list[tuple[str, str]]
    ) -> None:
        for call_id, content in results:
            messages.append(
                {"role": "tool", "tool_call_id": call_id, "content": content}
            )


def build_provider(config: Config, tools: list[ToolSpec]) -> Provider:
    """Crea el proveedor indicado en `modelo.proveedor`."""
    proveedor = config.modelo.proveedor
    if proveedor == "anthropic":
        return AnthropicProvider(config, tools)
    if proveedor == "groq":
        return GroqProvider(config, tools)
    raise BrainError(f"Proveedor de modelo desconocido: {proveedor}")
