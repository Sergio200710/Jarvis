"""Cliente del modelo de Anthropic, con la clave desde el entorno."""

from __future__ import annotations

import os

from jarvis.core.errors import BrainError

API_KEY_ENV = "ANTHROPIC_API_KEY"


def create_client(timeout: float):
    """Crea un cliente de Anthropic leyendo la clave de ANTHROPIC_API_KEY."""
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise BrainError(
            f"Falta la variable de entorno {API_KEY_ENV}. "
            "Configúrala para que pueda pensar."
        )
    try:
        import anthropic

        return anthropic.Anthropic(api_key=api_key, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - se informa por voz
        raise BrainError("No he podido crear el cliente del modelo.") from exc
