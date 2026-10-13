"""Pruebas de la logica de voz que no dependen de hardware."""

from __future__ import annotations

import numpy as np
import pytest

from jarvis.config import TTSConfig
from jarvis.voice.recorder import SilenceDetector, rms
from jarvis.voice.tts import Speaker, clean_for_speech

SAMPLE_RATE = 16_000
BLOCK_FRAMES = 480


def test_rms_silence_y_maximo() -> None:
    assert rms(np.zeros(10, dtype=np.float32)) == 0.0
    assert rms(np.full(10, 1.0, dtype=np.float32)) == pytest.approx(1.0)
    assert rms(np.array([1.0, -1.0], dtype=np.float32)) == pytest.approx(1.0)
    assert rms(np.array([], dtype=np.float32)) == 0.0


def _speech() -> np.ndarray:
    return np.full(BLOCK_FRAMES, 0.5, dtype=np.float32)


def _silence() -> np.ndarray:
    return np.zeros(BLOCK_FRAMES, dtype=np.float32)


def test_detector_para_tras_silencio_suficiente() -> None:
    detector = SilenceDetector(
        umbral=0.01, silencio_segundos=0.3, duracion_max_segundos=5, block_ms=30
    )
    assert detector.update(_speech()) is False
    assert detector.speech_started is True
    for _ in range(9):
        assert detector.update(_silence()) is False
    assert detector.update(_silence()) is True


def test_detector_para_por_duracion_maxima_sin_voz() -> None:
    detector = SilenceDetector(
        umbral=0.01, silencio_segundos=100.0, duracion_max_segundos=1, block_ms=30
    )
    for _ in range(33):
        assert detector.update(_silence()) is False
    assert detector.update(_silence()) is True
    assert detector.speech_started is False


def test_clean_for_speech_quita_markdown() -> None:
    texto = "```python\nprint('hola')\n```\n# Titulo\n\nEsto es **importante**."
    assert clean_for_speech(texto) == "Titulo Esto es importante."


def test_clean_for_speech_limita_a_tres_frases() -> None:
    texto = "Uno. Dos. Tres. Cuatro. Cinco."
    assert clean_for_speech(texto) == "Uno. Dos. Tres."


def test_clean_for_speech_texto_vacio() -> None:
    assert clean_for_speech("") == ""
    assert clean_for_speech("   ") == ""


class FakeEngine:
    """Motor de voz falso que registra lo que se le pide decir."""

    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.props: dict[str, object] = {}

    def setProperty(self, name: str, value: object) -> None:
        self.props[name] = value

    def getProperty(self, name: str):
        if name == "voices":
            return []
        return self.props.get(name)

    def say(self, text: str) -> None:
        self.spoken.append(text)

    def runAndWait(self) -> None:
        pass

    def stop(self) -> None:
        pass


def test_speaker_lee_texto_limpio() -> None:
    engine = FakeEngine()
    speaker = Speaker(TTSConfig(), engine_factory=lambda: engine)
    speaker.say("# Hola, **mundo**. Esto es dos. Esto es tres. Esto es cuatro.")
    speaker.flush()
    assert engine.spoken == ["Hola, mundo. Esto es dos. Esto es tres."]
    assert engine.props["rate"] == 180
    speaker.shutdown()


def test_speaker_ignora_texto_vacio() -> None:
    engine = FakeEngine()
    speaker = Speaker(TTSConfig(), engine_factory=lambda: engine)
    speaker.say("   ")
    speaker.flush()
    assert engine.spoken == []
    speaker.shutdown()
