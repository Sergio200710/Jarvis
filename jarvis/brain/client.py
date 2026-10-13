"""Cliente del modelo de Anthropic, con la clave desde el entorno."""

from __future__ import annotations

import os

from jarvis.core.errors import BrainError

API_KEY_ENV = "ANTHROPIC_API_KEY"


def create_client(timeout: float, api_key_env: str = API_KEY_ENV):
    """Crea un cliente de Anthropic leyendo la clave del entorno."""
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise BrainError(
            f"Falta la variable de entorno {api_key_env}. "
            "Configúrala para que pueda pensar."
        )
    try:
        import anthropic

        return anthropic.Anthropic(api_key=api_key, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - se informa por voz
        raise BrainError("No he podido crear el cliente del modelo.") from exc
