"""Permisos: gating por nivel de riesgo, confirmacion y auditoria."""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Protocol

from jarvis.config import Config

if TYPE_CHECKING:
    from jarvis.security.audit import AuditLog
    from jarvis.tools.base import ToolSpec

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Pasa a minusculas, quita acentos y deja solo letras, numeros y espacios."""
    if not text:
        return ""
    sin_acentos = unicodedata.normalize("NFKD", text)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    limpio = re.sub(r"[^a-z0-9 ]", " ", sin_acentos.lower())
    return re.sub(r"\s+", " ", limpio).strip()


def is_confirmation(text: str, palabras: list[str]) -> bool:
    """True si el texto contiene alguna de las palabras de confirmacion."""
    normalizado = normalize_text(text)
    if not normalizado:
        return False
    return any(normalize_text(palabra) in normalizado for palabra in palabras)


class ConfirmationDialog(Protocol):
    """Pregunta al usuario y responde si confirma."""

    def ask_yes_no(self, question: str) -> bool:
        """Formula una pregunta de si/no y devuelve la respuesta."""
        ...


class SecurityManager:
    """Decide si una herramienta puede ejecutarse y deja rastro en auditoria."""

    def __init__(
        self,
        config: Config,
        dialog: ConfirmationDialog | None = None,
        audit: "AuditLog | None" = None,
    ) -> None:
        self._config = config
        self._dialog = dialog
        self._audit = audit
        self._confirmar = set(config.seguridad.confirmar_riesgo)

    def _requiere_confirmacion(self, spec: "ToolSpec") -> bool:
        return spec.risk in self._confirmar

    def _registrar(
        self, request: str, spec: "ToolSpec", params: dict, result: str, estado: str
    ) -> None:
        if self._audit is not None:
            self._audit.log(request, spec, params, result, estado)

    def authorize(self, spec: "ToolSpec", params: dict, request: str) -> str:
        """Ejecuta la herramienta si esta permitida; si no, la rechaza."""
        if self._requiere_confirmacion(spec):
            pregunta = f"Voy a usar la herramienta {spec.name}. Di 'sí, hazlo' para confirmar."
            confirmado = self._dialog.ask_yes_no(pregunta) if self._dialog else False
            if not confirmado:
                logger.info("Accion '%s' cancelada por el usuario", spec.name)
                self._registrar(request, spec, params, "cancelado por el usuario", "cancelado")
                return "De acuerdo, lo dejo."

        try:
            resultado = spec.handler(**params)
        except Exception as exc:  # noqa: BLE001 - se informa por voz
            logger.exception("Fallo la herramienta %s", spec.name)
            self._registrar(request, spec, params, str(exc), "error")
            return f"La herramienta {spec.name} ha fallado."

        self._registrar(request, spec, params, resultado, "ejecutado")
        return resultado
