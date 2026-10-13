"""Excepciones propias de Jarvis."""

from __future__ import annotations


class JarvisError(Exception):
    """Error base de Jarvis."""


class ConfigError(JarvisError):
    """Configuracion ausente o invalida."""


class SecurityError(JarvisError):
    """Accion bloqueada por el modulo de seguridad."""


class ToolError(JarvisError):
    """Fallo al ejecutar una herramienta."""


class VoiceError(JarvisError):
    """Fallo en el subsistema de voz."""


class InputError(JarvisError):
    """Fallo al obtener la orden del usuario."""


class BrainError(JarvisError):
    """Fallo al consultar el modelo o ejecutar su bucle de herramientas."""
