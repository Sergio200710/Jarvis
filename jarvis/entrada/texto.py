"""Entrada por ventana emergente de texto (tkinter), sin microfono."""

from __future__ import annotations

import logging
import queue
import threading

from jarvis.core.state import JarvisState
from jarvis.entrada.base import InputResult, StateCallback

logger = logging.getLogger(__name__)


class TextInput:
    """Muestra una ventana con caja de texto y boton Enviar al activarse."""

    def __init__(self) -> None:
        self._queue: "queue.Queue[tuple[threading.Event, dict, threading.Event | None]]"
        self._queue = queue.Queue()
        self._root = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._ui_loop, name="input-ui", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5.0)

    def get_input(
        self, on_state: StateCallback, cancel: threading.Event | None = None
    ) -> InputResult:
        """Abre la ventana y espera a que el usuario envie o cancele."""
        on_state(JarvisState.LISTENING)
        done = threading.Event()
        box: dict[str, object] = {}
        self._queue.put((done, box, cancel))
        done.wait()
        text = box.get("text")
        text_str = text.strip() if isinstance(text, str) else ""
        cancelled = bool(box.get("cancelled"))
        return InputResult(text_str or None, cancelled, bool(text_str))

    def shutdown(self) -> None:
        """Cierra el bucle de la interfaz."""
        if self._root is not None:
            try:
                self._root.after(0, self._root.quit)
            except Exception:  # noqa: BLE001 - apagado best-effort
                pass
        self._thread.join(timeout=3.0)

    def _ui_loop(self) -> None:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        self._root = root
        self._ready.set()
        self._pump()
        root.mainloop()

    def _pump(self) -> None:
        try:
            while True:
                done, box, cancel = self._queue.get_nowait()
                self._show_dialog(done, box, cancel)
        except queue.Empty:
            pass
        if self._root is not None:
            self._root.after(80, self._pump)

    def _show_dialog(
        self,
        done: threading.Event,
        box: dict,
        cancel: threading.Event | None,
    ) -> None:
        import tkinter as tk

        root = self._root
        dlg = tk.Toplevel(root)
        dlg.title("Jarvis")
        dlg.attributes("-topmost", True)
        dlg.resizable(False, False)
        tk.Label(dlg, text="Escribe tu orden:").pack(padx=12, pady=(12, 4), anchor="w")
        entry = tk.Entry(dlg, width=52)
        entry.pack(padx=12, pady=4)

        closed = {"value": False}

        def finalize(text: str | None, cancelled: bool) -> None:
            if closed["value"]:
                return
            closed["value"] = True
            box["text"] = text
            box["cancelled"] = cancelled
            done.set()
            dlg.destroy()

        def submit(event=None) -> None:
            finalize(entry.get(), False)

        def on_cancel() -> None:
            finalize(None, True)

        buttons = tk.Frame(dlg)
        buttons.pack(padx=12, pady=(4, 12))
        tk.Button(buttons, text="Enviar", width=10, command=submit).pack(
            side="left", padx=4
        )
        tk.Button(buttons, text="Cancelar", width=10, command=on_cancel).pack(
            side="left", padx=4
        )
        entry.bind("<Return>", submit)
        dlg.protocol("WM_DELETE_WINDOW", on_cancel)

        def poll() -> None:
            if closed["value"]:
                return
            if cancel is not None and cancel.is_set():
                on_cancel()
                return
            root.after(120, poll)

        root.after(120, poll)
        dlg.lift()
        dlg.focus_force()
        dlg.grab_set()
