"""Pruebas de carga y validacion de la configuracion."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from jarvis.config import DEFAULT_CONFIG_YAML, Config, load_config


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_default_config_yaml_is_valid() -> None:
    data = yaml.safe_load(DEFAULT_CONFIG_YAML)
    config = Config(**data)
    assert config.modelo.nombre == "claude-sonnet-5-5"
    assert config.activacion.atajo == "ctrl+alt+j"
    assert config.voz.whisper.modelo == "small"
    assert config.voz.grabacion.duracion_max_segundos == 20
    assert config.seguridad.confirmar_riesgo == ["alto"]
    assert config.entrada.modo == "texto"
    assert config.arranque.inicio_automatico is None


def test_default_config_backslashes_are_single() -> None:
    config = Config(**yaml.safe_load(DEFAULT_CONFIG_YAML))
    assert config.carpetas_permitidas
    assert "\\" in config.carpetas_permitidas[0]
    assert "\\\\" not in config.carpetas_permitidas[0]


def test_load_config_from_file(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "modelo:\n  nombre: claude-haiku-5-5\n"
        "carpetas_permitidas:\n  - 'C:\\Temp'\n",
    )
    config = load_config(path)
    assert config.modelo.nombre == "claude-haiku-5-5"
    assert config.carpetas_permitidas == ["C:\\Temp"]
    assert config.activacion.atajo == "ctrl+alt+j"


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "no_existe.yaml")


def test_load_config_invalid_values(tmp_path: Path) -> None:
    path = _write(tmp_path, "modelo:\n  max_iteraciones_tools: 0\n")
    with pytest.raises(ValueError):
        load_config(path)


def test_load_config_empty_file_uses_defaults(tmp_path: Path) -> None:
    path = _write(tmp_path, "")
    config = load_config(path)
    assert config.modelo.nombre == "claude-sonnet-5-5"
