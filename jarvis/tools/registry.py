"""Registro central de herramientas y autodescubrimiento."""

from __future__ import annotations

import importlib
import logging
import pkgutil

from jarvis.tools.base import ToolSpec

logger = logging.getLogger(__name__)

_NO_HERRAMIENTAS = {"base", "registry", "context"}


class ToolRegistry:
    """Guarda las herramientas y las ofrece al cerebro."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Anade una herramienta; falla si el nombre ya existe."""
        if spec.name in self._tools:
            raise ValueError(f"Herramienta duplicada: {spec.name}")
        self._tools[spec.name] = spec
        logger.debug("Herramienta registrada: %s (%s)", spec.name, spec.risk)

    def get(self, name: str) -> ToolSpec | None:
        """Devuelve la herramienta por nombre, o None."""
        return self._tools.get(name)

    def specs(self) -> list[ToolSpec]:
        """Todas las herramientas registradas."""
        return list(self._tools.values())

    def names(self) -> list[str]:
        """Nombres de las herramientas registradas."""
        return list(self._tools)

    def schemas(self) -> list[dict]:
        """Esquemas listos para pasar al modelo."""
        return [spec.to_schema() for spec in self._tools.values()]


def discover(package: str = "jarvis.tools") -> ToolRegistry:
    """Crea un registro escaneando los modulos de herramientas con atributo SPEC."""
    registry = ToolRegistry()
    paquete = importlib.import_module(package)
    modulos = sorted(
        info.name for info in pkgutil.iter_modules(paquete.__path__)
        if not info.name.startswith("_")
    )
    for nombre in modulos:
        if nombre in _NO_HERRAMIENTAS:
            continue
        modulo = importlib.import_module(f"{package}.{nombre}")
        spec = getattr(modulo, "SPEC", None)
        if isinstance(spec, ToolSpec):
            registry.register(spec)
        else:
            logger.debug("Modulo sin SPEC ignorado: %s", nombre)
    logger.info("Herramientas descubiertas: %s", ", ".join(registry.names()))
    return registry
