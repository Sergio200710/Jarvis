"""Pruebas del gating por riesgo y las confirmaciones."""

from __future__ import annotations

from jarvis.config import Config
from jarvis.security.permissions import (
    SecurityManager,
    is_confirmation,
    normalize_text,
)
from jarvis.tools.base import ToolSpec


class FakeDialog:
    def __init__(self, respuesta: bool) -> None:
        self.respuesta = respuesta
        self.preguntas: list[str] = []

    def ask_yes_no(self, question: str) -> bool:
        self.preguntas.append(question)
        return self.respuesta


class FakeAudit:
    def __init__(self) -> None:
        self.registros: list[dict] = []

    def log(self, request, spec, params, result, estado="ejecutado") -> None:
        self.registros.append(
            {
                "peticion": request,
                "herramienta": spec.name,
                "estado": estado,
                "resultado": result,
            }
        )


def _spec(risk: str, handler) -> ToolSpec:
    return ToolSpec(
        name="peligrosa",
        description="descripcion",
        parameters={"type": "object", "properties": {}},
        risk=risk,  # type: ignore[arg-type]
        handler=handler,
    )


def test_normalize_text_quita_acentos_y_signos() -> None:
    assert normalize_text("Sí, hazlo!") == "si hazlo"
    assert normalize_text("  VALE,  adelante. ") == "vale adelante"


def test_is_confirmation() -> None:
    palabras = ["si hazlo", "adelante"]
    assert is_confirmation("sí, hazlo", palabras)
    assert is_confirmation("Si hazlo.", palabras)
    assert is_confirmation("vale, adelante", palabras)
    assert not is_confirmation("no, gracias", palabras)
    assert not is_confirmation("", palabras)


def test_riesgo_bajo_no_pide_confirmacion() -> None:
    dialog = FakeDialog(False)
    audit = FakeAudit()
    sm = SecurityManager(Config(), dialog=dialog, audit=audit)

    resultado = sm.authorize(_spec("bajo", lambda **k: "ok"), {}, "peticion")

    assert resultado == "ok"
    assert dialog.preguntas == []
    assert audit.registros[-1]["estado"] == "ejecutado"


def test_riesgo_alto_confirmado_ejecuta() -> None:
    dialog = FakeDialog(True)
    audit = FakeAudit()
    sm = SecurityManager(Config(), dialog=dialog, audit=audit)

    resultado = sm.authorize(_spec("alto", lambda **k: "hecho"), {}, "peticion")

    assert resultado == "hecho"
    assert len(dialog.preguntas) == 1
    assert audit.registros[-1]["estado"] == "ejecutado"


def test_riesgo_alto_no_confirmado_no_ejecuta() -> None:
    dialog = FakeDialog(False)
    audit = FakeAudit()
    sm = SecurityManager(Config(), dialog=dialog, audit=audit)
    llamado: list[int] = []

    resultado = sm.authorize(
        _spec("alto", lambda **k: llamado.append(1) or "hecho"), {}, "peticion"
    )

    assert "lo dejo" in resultado.lower()
    assert llamado == []
    assert audit.registros[-1]["estado"] == "cancelado"


def test_sin_dialogo_el_riesgo_alto_se_rechaza() -> None:
    audit = FakeAudit()
    sm = SecurityManager(Config(), dialog=None, audit=audit)
    resultado = sm.authorize(_spec("alto", lambda **k: "hecho"), {}, "peticion")
    assert "lo dejo" in resultado.lower()
    assert audit.registros[-1]["estado"] == "cancelado"


def test_herramienta_que_falla_se_registra_como_error() -> None:
    def boom(**kwargs):
        raise RuntimeError("explotó")

    audit = FakeAudit()
    sm = SecurityManager(Config(), dialog=FakeDialog(True), audit=audit)

    resultado = sm.authorize(_spec("bajo", boom), {}, "peticion")

    assert "ha fallado" in resultado.lower()
    assert audit.registros[-1]["estado"] == "error"
