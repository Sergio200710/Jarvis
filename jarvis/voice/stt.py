"""Voz a texto local con faster-whisper."""

from __future__ import annotations

import logging

import numpy as np

from jarvis.config import VozConfig
from jarvis.core.errors import VoiceError

logger = logging.getLogger(__name__)


class Transcriber:
    """Envuelve faster-whisper cargando el modelo solo en el primer uso."""

    def __init__(self, config: VozConfig) -> None:
        self._config = config
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise VoiceError("faster-whisper no esta instalado.") from exc
        logger.info("Cargando modelo whisper '%s'", self._config.whisper.modelo)
        try:
            self._model = WhisperModel(
                self._config.whisper.modelo,
                device=self._config.whisper.dispositivo,
                compute_type=self._config.whisper.compute_type,
            )
        except Exception as exc:  # noqa: BLE001 - se informa por voz
            raise VoiceError(
                f"No he podido cargar el modelo de voz '{self._config.whisper.modelo}'."
            ) from exc
        return self._model

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio mono float32 a texto en el idioma configurado."""
        if audio is None or audio.size == 0:
            return ""
        model = self._ensure_model()
        try:
            segments, _info = model.transcribe(
                audio,
                language=self._config.idioma,
                beam_size=5,
                vad_filter=True,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:  # noqa: BLE001 - se informa por voz
            raise VoiceError("No he podido transcribir el audio.") from exc
