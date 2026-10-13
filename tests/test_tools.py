"""Pruebas de las herramientas iniciales."""

from __future__ import annotations

import re
from pathlib import Path

import jarvis.tools.abrir_app as abrir_app
import jarvis.tools.buscar_web as buscar_web
import jarvis.tools.hora_y_fecha as hora_y_fecha
import jarvis.tools.listar_archivos as listar_archivos
from jarvis.config import Config
from jarvis.tools import context


def test_hora_y_fecha(config: Config) -> None:
    context.set_config(config)
    salida = hora_y_fecha.run()
    assert "Hoy es" in salida
    assert "son las" in salida
    assert re.search(r"\d{2}:\d{2}", salida)


def test_abrir_app_desconocida(config: Config) -> None:
    context.set_config(config)
    salida = abrir_app.run(nombre="spotify")
    assert "no tengo registrada" in salida.lower()


def test_abrir_app_sin_nombre(config: Config) -> None:
    context.set_config(config)
    assert "no me has dicho" in abrir_app.run().lower()


def test_abrir_app_lanza_programa(config: Config, monkeypatch) -> None:
    context.set_config(config)
    capturado: dict = {}

    def fake_popen(args, **kwargs):
        capturado["args"] = args
        capturado["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(abrir_app.subprocess, "Popen", fake_popen)
    salida = abrir_app.run(nombre="Notepad")

    assert "he abierto notepad" in salida.lower()
    assert capturado["args"] == ["notepad.exe"]
    assert capturado["kwargs"]["shell"] is False


def test_buscar_web_abre_url(monkeypatch) -> None:
    capturado: dict = {}

    def fake_open(url, new=0):
        capturado["url"] = url
        return True

    monkeypatch.setattr(buscar_web.webbrowser, "open", fake_open)
    salida = buscar_web.run(consulta="clima madrid")

    assert "clima+madrid" in capturado["url"]
    assert "he buscado" in salida.lower()


def test_buscar_web_sin_consulta() -> None:
    assert "no me has dicho" in buscar_web.run().lower()


def test_listar_archivos(tmp_path: Path) -> None:
    (tmp_path / "notas.txt").write_text("hola", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    context.set_config(Config(carpetas_permitidas=[str(tmp_path)]))

    salida = listar_archivos.run(ruta=str(tmp_path))

    assert "notas.txt" in salida
    assert "sub" in salida
    assert "archivo" in salida
    assert "carpeta" in salida


def test_listar_archivos_fuera_rechazada(tmp_path: Path) -> None:
    permitida = tmp_path / "permitida"
    permitida.mkdir()
    context.set_config(Config(carpetas_permitidas=[str(permitida)]))

    salida = listar_archivos.run(ruta=str(tmp_path))

    assert "fuera de las carpetas permitidas" in salida.lower()


def test_listar_archivos_carpeta_inexistente(tmp_path: Path) -> None:
    context.set_config(Config(carpetas_permitidas=[str(tmp_path)]))
    salida = listar_archivos.run(ruta=str(tmp_path / "noexiste"))
    assert "no encuentro" in salida.lower()
