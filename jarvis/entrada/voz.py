"""Entrada por voz: grabacion y transcripcion (requiere microfono)."""

from __future__ import annotations

import logging
import threading

from jarvis.config import VozConfig
from jarvis.core.state import JarvisState
from jarvis.entrada.base import InputResult, StateCallback
from jarvis.voice.recorder import Recorder
from jarvis.voice.stt import Transcriber

logger = logging.getLogger(__name__)


class VoiceInput:
    """Adapta el grabador y el transcriptor al contrato de entrada."""

    def __init__(self, config: VozConfig) -> None:
        self._config = config
        self._recorder = Recorder(config)
        self._transcriber = Transcriber(config)

    def get_input(
        self, on_state: StateCallback, cancel: threading.Event | None = None
    ) -> InputResult:
        """Graba hasta silencio/cancelacion y devuelve la transcripcion."""
        on_state(JarvisState.LISTENING)
        resultado = self._recorder.record(cancel)
        if resultado.cancelled:
            return InputResult(None, True, False)
        if not resultado.had_speech or resultado.audio is None:
            return InputResult(None, False, False)
        on_state(JarvisState.TRANSCRIBING)
        texto = (self._transcriber.transcribe(resultado.audio) or "").strip()
        return InputResult(texto or None, False, bool(texto))

    def shutdown(self) -> None:
        """Sin recursos persistentes que liberar."""
        return None
