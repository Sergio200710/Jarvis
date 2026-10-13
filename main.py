"""Punto de entrada de Jarvis."""

from __future__ import annotations

import logging
import queue
import sys
import threading

from jarvis.activation.hotkey import HotkeyListener
from jarvis.activation.tray import TrayActivator
from jarvis.brain.agent import Brain
from jarvis.config import Config, load_config
from jarvis.core.orchestrator import Orchestrator
from jarvis.core.state import Event
from jarvis.entrada import build_input
from jarvis.security.audit import AuditLog
from jarvis.security.permissions import SecurityManager
from jarvis.tools import context as tools_context
from jarvis.tools.registry import ToolRegistry, discover
from jarvis.utils import autostart
from jarvis.utils.logging_setup import setup_logging
from jarvis.voice.tts import Speaker

logger = logging.getLogger(__name__)


def build_registry() -> ToolRegistry:
    """Registra automaticamente toda herramienta con SPEC en jarvis/tools."""
    return discover()


def main() -> int:
    """Carga la configuracion y arranca atajo, bandeja, voz y orquestador."""
    try:
        config: Config = load_config()
    except Exception as exc:  # noqa: BLE001 - se informa y se sale con codigo 1
        print(f"No se pudo cargar la configuracion: {exc}", file=sys.stderr)
        return 1

    setup_logging()
    logger.info("Iniciando Jarvis")

    if config.arranque.inicio_automatico is not None:
        try:
            autostart.set_enabled(config.arranque.inicio_automatico)
        except OSError as exc:
            logger.warning("No pude ajustar el arranque automatico: %s", exc)

    tools_context.set_config(config)
    provider = build_input(config)
    speaker = Speaker(config.voz.tts)

    events: "queue.Queue[Event]" = queue.Queue()
    orchestrator = Orchestrator(config, events, provider=provider, speaker=speaker)

    audit = AuditLog(config.seguridad.ruta_audit)
    security = SecurityManager(config, dialog=orchestrator, audit=audit)
    brain = Brain(config, build_registry(), security=security)
    orchestrator.set_brain(brain)

    hotkey = HotkeyListener(config.activacion.atajo, orchestrator.toggle)
    hotkey.start()

    tray: TrayActivator | None = None
    if config.activacion.bandeja:
        tray = TrayActivator(orchestrator)

    def shutdown() -> None:
        if tray is not None:
            tray.stop()
        speaker.shutdown()
        provider.shutdown()

    orchestrator.set_on_shutdown(shutdown)

    speaker.say("Estoy listo")

    try:
        if tray is not None:
            worker = threading.Thread(
                target=orchestrator.run, name="orchestrator", daemon=True
            )
            worker.start()
            tray.run()
            worker.join(timeout=5)
        else:
            orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Interrupcion por teclado, apagando")
        orchestrator.stop()
    finally:
        hotkey.stop()
        logger.info("Jarvis detenido")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
