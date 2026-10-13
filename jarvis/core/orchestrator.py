"""Orquestador: bucle principal y maquina de estados de Jarvis."""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from jarvis.config import Config
from jarvis.core.errors import BrainError, InputError, VoiceError
from jarvis.core.state import Event, EventKind, JarvisState
from jarvis.security.permissions import is_confirmation

if TYPE_CHECKING:
    from jarvis.brain.agent import Brain
    from jarvis.entrada.base import InputProvider
    from jarvis.voice.tts import Speaker

logger = logging.getLogger(__name__)


class Orchestrator:
    """Consume eventos de una cola y reacciona segun el estado actual."""

    def __init__(
        self,
        config: Config,
        events: "queue.Queue[Event]",
        provider: "InputProvider | None" = None,
        speaker: "Speaker | None" = None,
        brain: "Brain | None" = None,
        on_shutdown: Callable[[], None] | None = None,
    ) -> None:
        self._config = config
        self._events = events
        self._provider = provider
        self._speaker = speaker
        self._brain = brain
        self._on_shutdown = on_shutdown
        self._running = False
        self._state = JarvisState.IDLE
        self._cancel = threading.Event()

    @property
    def state(self) -> JarvisState:
        """Estado actual del orquestador."""
        return self._state

    def set_on_shutdown(self, callback: Callable[[], None]) -> None:
        """Registra el callback que se ejecuta al apagarse."""
        self._on_shutdown = callback

    def set_brain(self, brain: "Brain") -> None:
        """Asigna el cerebro una vez construido."""
        self._brain = brain

    def submit(self, event: Event) -> None:
        """Encola un evento para el bucle principal."""
        self._events.put(event)

    def toggle(self) -> None:
        """Activa Jarvis o cancela la entrada en curso (hilo de atajo/bandeja)."""
        if self._state in (
            JarvisState.LISTENING,
            JarvisState.TRANSCRIBING,
            JarvisState.CONFIRMING,
        ):
            self._cancel.set()
        else:
            self.submit(Event(EventKind.ACTIVATE))

    def ask_yes_no(self, question: str) -> bool:
        """Formula una pregunta y devuelve True si el usuario confirma."""
        if self._provider is None or self._speaker is None:
            return False
        self._state = JarvisState.CONFIRMING
        self._speaker.say(question)
        try:
            entrada = self._provider.get_input(lambda _s: None, self._cancel)
        except (VoiceError, InputError) as exc:
            logger.error("No pude pedir confirmacion: %s", exc)
            return False
        if entrada.cancelled or not entrada.text:
            return False
        return is_confirmation(
            entrada.text, self._config.seguridad.palabras_confirmacion
        )

    def stop(self) -> None:
        """Solicita el apagado ordenado del orquestador."""
        self._cancel.set()
        self.submit(Event(EventKind.SHUTDOWN))

    def run(self) -> None:
        """Bucle principal. Bloquea hasta recibir un evento de apagado."""
        self._running = True
        logger.info("Orquestador iniciado en estado %s", self._state.name)
        while self._running:
            try:
                event = self._events.get(timeout=0.5)
            except queue.Empty:
                continue
            self._handle(event)
        logger.info("Orquestador detenido")

    def _handle(self, event: Event) -> None:
        if event.kind is EventKind.SHUTDOWN:
            self._running = False
            logger.info("Recibida senal de apagado")
            if self._on_shutdown is not None:
                self._on_shutdown()
            return
        if event.kind is EventKind.ACTIVATE:
            self._on_activate()
            return
        logger.debug("Evento ignorado en estado %s: %s", self._state.name, event.kind)

    def _set_state(self, state: JarvisState) -> None:
        self._state = state

    def _on_activate(self) -> None:
        """Pide una orden, la procesa con el cerebro y responde por voz."""
        if self._provider is None or self._speaker is None:
            print("activado")
            logger.info("Jarvis activado (sin voz configurada)")
            return

        self._cancel.clear()
        try:
            entrada = self._provider.get_input(self._set_state, self._cancel)
        except (VoiceError, InputError) as exc:
            self._speak_error(str(exc))
            return

        if entrada.cancelled:
            logger.info("Entrada cancelada por el usuario")
            self._state = JarvisState.IDLE
            return
        if not entrada.had_input or not entrada.text:
            self._finish_with("No he recibido ninguna orden.")
            return

        if self._brain is None:
            self._state = JarvisState.SPEAKING
            self._speaker.say(entrada.text)
            self._state = JarvisState.IDLE
            return

        self._state = JarvisState.THINKING
        try:
            respuesta = self._brain.respond(entrada.text)
        except BrainError as exc:
            self._speak_error(str(exc))
            return

        self._finish_with(respuesta)

    def _finish_with(self, text: str) -> None:
        self._state = JarvisState.SPEAKING
        if self._speaker is not None:
            self._speaker.say(text)
        self._state = JarvisState.IDLE

    def _speak_error(self, message: str) -> None:
        logger.error("Error: %s", message)
        self._finish_with(message)
