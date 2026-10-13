"""Pruebas del arranque automatico con Windows (registro simulado)."""

from __future__ import annotations

from jarvis.utils import autostart


class FakeKey:
    def __init__(self, store: dict, path: str) -> None:
        self._store = store
        self._path = path

    def __enter__(self) -> "FakeKey":
        return self

    def __exit__(self, *args) -> bool:
        return False


class FakeWinreg:
    HKEY_CURRENT_USER = object()
    REG_SZ = 1
    KEY_SET_VALUE = 2

    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def CreateKey(self, root, path):
        return FakeKey(self.values, path)

    def OpenKey(self, root, path, reserved=0, access=0):
        return FakeKey(self.values, path)

    def SetValueEx(self, key, name, reserved, tipo, value):
        self.values[(key._path, name)] = value

    def QueryValueEx(self, key, name):
        if (key._path, name) not in self.values:
            raise FileNotFoundError(name)
        return self.values[(key._path, name)], self.REG_SZ

    def DeleteValue(self, key, name):
        if (key._path, name) not in self.values:
            raise FileNotFoundError(name)
        del self.values[(key._path, name)]


def test_enable_disable_is_enabled(monkeypatch) -> None:
    fake = FakeWinreg()
    monkeypatch.setattr(autostart, "winreg", fake)

    assert autostart.is_enabled() is False
    autostart.enable()
    assert autostart.is_enabled() is True
    stored = fake.values[(autostart.RUN_KEY, autostart.APP_NAME)]
    assert stored == autostart.command()
    autostart.disable()
    assert autostart.is_enabled() is False


def test_set_enabled(monkeypatch) -> None:
    monkeypatch.setattr(autostart, "winreg", FakeWinreg())
    autostart.set_enabled(True)
    assert autostart.is_enabled() is True
    autostart.set_enabled(False)
    assert autostart.is_enabled() is False


def test_disable_sin_entrada_no_falla(monkeypatch) -> None:
    monkeypatch.setattr(autostart, "winreg", FakeWinreg())
    autostart.disable()


def test_command_frozen(monkeypatch) -> None:
    monkeypatch.setattr(autostart.sys, "frozen", True, raising=False)
    assert autostart.command() == f'"{autostart.sys.executable}"'


def test_command_dev_apunta_a_main(monkeypatch) -> None:
    monkeypatch.delattr(autostart.sys, "frozen", raising=False)
    assert autostart.command().endswith('main.py"')
