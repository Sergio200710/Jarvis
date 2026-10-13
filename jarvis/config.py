"""Carga, validacion y localizacion de la configuracion de Jarvis."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

DEFAULT_CONFIG_YAML = """\
modelo:
  proveedor: groq
  nombre: openai/gpt-oss-120b
  max_iteraciones_tools: 5
  timeout_segundos: 30

voz:
  idioma: es
  whisper:
    modelo: small
    dispositivo: cpu
    compute_type: int8
  tts:
    voz: null
    velocidad: 180
    volumen: 1.0
  grabacion:
    duracion_max_segundos: 20
    umbral_silencio: 0.01
    silencio_segundos: 1.2

entrada:
  modo: texto

arranque:
  inicio_automatico: null

activacion:
  atajo: "ctrl+alt+j"
  bandeja: true

carpetas_permitidas:
  - "C:\\\\Users\\\\sergi\\\\Documents"
  - "C:\\\\Users\\\\sergi\\\\Desktop"

apps_lista_blanca:
  - nombre: notepad
    ruta: notepad.exe
  - nombre: calculadora
    ruta: calc.exe

seguridad:
  confirmar_riesgo:
    - alto
  palabras_confirmacion:
    - "si, hazlo"
    - "sí, hazlo"
    - confirma
    - adelante
  ruta_audit: logs/audit.log
"""


class ModeloConfig(BaseModel):
    """Ajustes del modelo de lenguaje."""

    proveedor: Literal["anthropic", "groq"] = "groq"
    nombre: str = "openai/gpt-oss-120b"
    max_iteraciones_tools: int = Field(default=5, ge=1, le=20)
    timeout_segundos: int = Field(default=30, ge=1, le=300)
    api_key_env: str | None = None
    base_url: str | None = None


class WhisperConfig(BaseModel):
    """Ajustes del motor de voz a texto."""

    modelo: str = "small"
    dispositivo: str = "cpu"
    compute_type: str = "int8"


class TTSConfig(BaseModel):
    """Ajustes del motor de texto a voz."""

    voz: str | None = None
    velocidad: int = Field(default=180, ge=50, le=400)
    volumen: float = Field(default=1.0, ge=0.0, le=1.0)


class GrabacionConfig(BaseModel):
    """Ajustes de captura de audio."""

    duracion_max_segundos: int = Field(default=20, ge=1, le=120)
    umbral_silencio: float = Field(default=0.01, ge=0.0, le=1.0)
    silencio_segundos: float = Field(default=1.2, ge=0.1, le=10.0)


class VozConfig(BaseModel):
    """Ajustes completos del subsistema de voz."""

    idioma: str = "es"
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    grabacion: GrabacionConfig = Field(default_factory=GrabacionConfig)


class ActivacionConfig(BaseModel):
    """Ajustes de atajo global y bandeja."""

    atajo: str = "ctrl+alt+j"
    bandeja: bool = True


class EntradaConfig(BaseModel):
    """Modo de entrada de ordenes: por texto (ventana) o por voz (microfono)."""

    modo: Literal["texto", "voz"] = "texto"

    @property
    def es_voz(self) -> bool:
        """True si la entrada es por voz."""
        return self.modo == "voz"


class ArranqueConfig(BaseModel):
    """Ajustes de arranque con Windows."""

    inicio_automatico: bool | None = None


class AppWhitelistItem(BaseModel):
    """Aplicacion permitida para abrir."""

    nombre: str
    ruta: str


class SeguridadConfig(BaseModel):
    """Ajustes del modulo de seguridad."""

    confirmar_riesgo: list[str] = Field(default_factory=lambda: ["alto"])
    palabras_confirmacion: list[str] = Field(
        default_factory=lambda: ["si, hazlo", "sí, hazlo", "confirma", "adelante"]
    )
    ruta_audit: str = "logs/audit.log"


class Config(BaseModel):
    """Configuracion completa de Jarvis."""

    modelo: ModeloConfig = Field(default_factory=ModeloConfig)
    voz: VozConfig = Field(default_factory=VozConfig)
    entrada: EntradaConfig = Field(default_factory=EntradaConfig)
    arranque: ArranqueConfig = Field(default_factory=ArranqueConfig)
    activacion: ActivacionConfig = Field(default_factory=ActivacionConfig)
    carpetas_permitidas: list[str] = Field(default_factory=list)
    apps_lista_blanca: list[AppWhitelistItem] = Field(default_factory=list)
    seguridad: SeguridadConfig = Field(default_factory=SeguridadConfig)


def is_frozen() -> bool:
    """Indica si el proceso corre empaquetado con PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def get_config_dir() -> Path:
    """Devuelve la carpeta de configuracion segun el modo de ejecucion."""
    if is_frozen():
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "Jarvis"
    return Path(__file__).resolve().parent.parent


def get_config_path() -> Path:
    """Ruta absoluta del archivo config.yaml."""
    return get_config_dir() / "config.yaml"


def ensure_config_exists() -> Path:
    """Crea una configuracion por defecto si no existe (modo empaquetado)."""
    path = get_config_path()
    if not path.exists() and is_frozen():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    return path


def load_config(path: str | Path | None = None) -> Config:
    """Carga y valida config.yaml, lanzando un error claro si es invalida."""
    config_path = Path(path) if path is not None else ensure_config_exists()
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontro la configuracion: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        return Config(**raw)
    except ValidationError as exc:
        raise ValueError(f"Configuracion invalida en {config_path}:\n{exc}") from exc
