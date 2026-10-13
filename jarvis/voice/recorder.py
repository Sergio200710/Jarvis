"""Grabacion de audio con deteccion de silencio y cancelacion."""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

from jarvis.config import VozConfig
from jarvis.core.errors import VoiceError

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
BLOCK_MS = 30


def rms(block: np.ndarray) -> float:
    """Energia RMS de un bloque de audio normalizado en [-1, 1]."""
    if block.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(block, dtype=np.float64))))


class SilenceDetector:
    """Decide cuando terminar la grabacion segun energia y duracion."""

    def __init__(
        self,
        umbral: float,
        silencio_segundos: float,
        duracion_max_segundos: int,
        block_ms: int = BLOCK_MS,
    ) -> None:
        self._umbral = umbral
        self._bloques_silencio_necesarios = max(
            1, math.ceil(silencio_segundos * 1000 / block_ms)
        )
        self._bloques_max = max(1, math.ceil(duracion_max_segundos * 1000 / block_ms))
        self._bloques = 0
        self._silencio = 0
        self.speech_started = False

    def update(self, block: np.ndarray) -> bool:
        """Procesa un bloque y devuelve True si hay que parar de grabar."""
        self._bloques += 1
        if rms(block) >= self._umbral:
            self.speech_started = True
            self._silencio = 0
        elif self.speech_started:
            self._silencio += 1

        if self._bloques >= self._bloques_max:
            return True
        return (
            self.speech_started
            and self._silencio >= self._bloques_silencio_necesarios
        )


@dataclass(frozen=True)
class RecordResult:
    """Resultado de una grabacion."""

    audio: np.ndarray | None
    cancelled: bool
    had_speech: bool


class Recorder:
    """Captura audio del microfono hasta detectar silencio, cancelacion o tope."""

    def __init__(self, config: VozConfig) -> None:
        self._config = config

    def record(self, cancel_event: threading.Event | None = None) -> RecordResult:
        """Graba y devuelve el audio (float32 mono). Lanza VoiceError si falla."""
        grabacion = self._config.grabacion
        block_frames = int(SAMPLE_RATE * BLOCK_MS / 1000)
        detector = SilenceDetector(
            umbral=grabacion.umbral_silencio,
            silencio_segundos=grabacion.silencio_segundos,
            duracion_max_segundos=grabacion.duracion_max_segundos,
        )
        blocks: list[np.ndarray] = []
        cancelled = False

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=block_frames,
            ) as stream:
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        cancelled = True
                        break
                    block, overflowed = stream.read(block_frames)
                    if overflowed:
                        logger.warning("Desbordamiento del buffer de audio")
                    mono = block[:, 0]
                    blocks.append(mono.copy())
                    if detector.update(mono):
                        break
        except sd.PortAudioError as exc:
            raise VoiceError(
                "No puedo acceder al microfono. Revisa el dispositivo de entrada."
            ) from exc

        if cancelled or not blocks:
            return RecordResult(None, cancelled, detector.speech_started)
        audio = np.concatenate(blocks) if len(blocks) > 1 else blocks[0]
        return RecordResult(audio, cancelled, detector.speech_started)
