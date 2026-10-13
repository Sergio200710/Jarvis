"""Selecciona la fuente de entrada segun la configuracion."""

from __future__ import annotations

from jarvis.config import Config
from jarvis.entrada.base import InputProvider
from jarvis.entrada.texto import TextInput
from jarvis.entrada.voz import VoiceInput


def build_input(config: Config) -> InputProvider:
    """Devuelve la entrada por voz o por texto segun config.yaml."""
    if config.entrada.es_voz:
        return VoiceInput(config.voz)
    return TextInput()
