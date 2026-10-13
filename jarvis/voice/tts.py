"""Texto a voz con pyttsx3, serializado en un hilo propio."""

from __future__ import annotations

import logging
import queue
import re
import threading
from collections.abc import Callable

from jarvis.config import TTSConfig

logger = logging.getLogger(__name__)


def clean_for_speech(text: str, max_sentences: int = 3) -> str:
    """Limpia markdown y limita el texto a frases cortas para leer en voz alta."""
    if not text:
        return ""
    cleaned = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"[*_#>~|]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned).strip()
    if not cleaned:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(sentences[:max_sentences]).strip()


def _default_engine_factory():
    import pyttsx3

    return pyttsx3.init()


class Speaker:
    """Lee texto en voz alta desde un hilo dedicado para no bloquear al resto."""

    def __init__(
        self,
        config: TTSConfig,
        engine_factory: Callable[[], object] | None = None,
    ) -> None:
        self._config = config
        self._factory = engine_factory or _default_engine_factory
        self._queue: "queue.Queue[tuple[str, str | None, threading.Event | None]]"
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, name="tts", daemon=True)
        self._thread.start()

    def say(self, text: str) -> None:
        """Encola un texto limpio para ser leido."""
        cleaned = clean_for_speech(text)
        if cleaned:
            self._queue.put(("say", cleaned, None))

    def flush(self, timeout: float = 60.0) -> None:
        """Espera a que se lean todos los textos encolados."""
        done = threading.Event()
        self._queue.put(("flush", None, done))
        done.wait(timeout)

    def shutdown(self, timeout: float = 10.0) -> None:
        """Detiene el hilo tras vaciar la cola."""
        done = threading.Event()
        self._queue.put(("stop", None, done))
        done.wait(timeout)
        self._thread.join(timeout=timeout)

    def _select_voice(self, engine, nombre: str) -> None:
        objetivo = nombre.lower()
        for voice in engine.getProperty("voices"):
            if objetivo in voice.name.lower():
                engine.setProperty("voice", voice.id)
                return
        logger.warning("No encontre la voz '%s'; uso la voz por defecto", nombre)

    def _speak_blocking(self, text: str) -> None:
        engine = self._factory()
        try:
            engine.setProperty("rate", self._config.velocidad)
            engine.setProperty("volume", self._config.volumen)
            if self._config.voz:
                self._select_voice(engine, self._config.voz)
            engine.say(text)
            engine.runAndWait()
        finally:
            try:
                engine.stop()
            except Exception:  # noqa: BLE001 - limpieza best-effort
                pass

    def _worker(self) -> None:
        while True:
            kind, payload, done = self._queue.get()
            if kind == "stop":
                if done is not None:
                    done.set()
                return
            if kind == "flush":
                if done is not None:
                    done.set()
                continue
            if kind == "say" and payload is not None:
                try:
                    self._speak_blocking(payload)
                except Exception:  # noqa: BLE001 - nunca debe tumbar el hilo
                    logger.exception("Fallo al reproducir voz")
                finally:
                    if done is not None:
                        done.set()
