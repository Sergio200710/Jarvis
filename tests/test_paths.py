"""Pruebas de validacion de rutas permitidas."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.errors import SecurityError
from jarvis.security.paths import ensure_allowed, is_within


def test_is_within_dentro_y_raiz(tmp_path: Path) -> None:
    hijo = tmp_path / "sub" / "a.txt"
    assert is_within(hijo, tmp_path)
    assert is_within(tmp_path, tmp_path)
    assert not is_within(tmp_path.parent, tmp_path)


def test_ensure_allowed_dentro(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    resultado = ensure_allowed(str(tmp_path / "sub"), [str(tmp_path)])
    assert resultado == (tmp_path / "sub").resolve()


def test_ensure_allowed_escapa_con_punto_punto(tmp_path: Path) -> None:
    permitida = tmp_path / "permitida"
    permitida.mkdir()
    with pytest.raises(SecurityError):
        ensure_allowed(str(permitida / ".." / "secreta"), [str(permitida)])


def test_ensure_allowed_relativa_usa_primera_carpeta(tmp_path: Path) -> None:
    permitida = tmp_path / "permitida"
    (permitida / "sub").mkdir(parents=True)
    resultado = ensure_allowed("sub", [str(permitida)])
    assert resultado == (permitida / "sub").resolve()


def test_ensure_allowed_fuera(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_allowed(str(tmp_path.parent), [str(tmp_path / "otra")])


def test_ensure_allowed_sin_ruta_ni_carpetas(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_allowed("", [str(tmp_path)])
    with pytest.raises(SecurityError):
        ensure_allowed(str(tmp_path), [])
