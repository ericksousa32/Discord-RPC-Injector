"""Controls the Discord connection, running the engine off the GUI thread."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject, Signal

from ..i18n import tr
from .models import Presence


def thread_runner(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, daemon=True).start()


class LogEntry:
    __slots__ = ("time", "level", "message")

    def __init__(self, level: str, message: str):
        self.time = datetime.now()
        self.level = level
        self.message = message


class PresenceController(QObject):
    """States: ``disconnected`` → ``connecting`` → ``connected``."""

    state_changed = Signal(str)
    applied = Signal()
    cleared = Signal()
    failed = Signal(str, str)          # title, message
    logged = Signal(object)            # LogEntry
    _done = Signal(object)             # callback run on the GUI thread

    def __init__(self, ipc_factory=None, runner: Callable = thread_runner, parent=None):
        super().__init__(parent)
        if ipc_factory is None:
            from .engine import DiscordIPC
            ipc_factory = DiscordIPC
        self._ipc_factory = ipc_factory
        self._run = runner
        self.ipc = None
        self.state = "disconnected"
        self.socket_path = ""
        self.start_ts: int | None = None
        self.active_presence: Presence | None = None
        self.history: list[LogEntry] = []
        self._done.connect(lambda cb: cb())

    # ── util ─────────────────────────────────────────────────────────────────
    @property
    def connected(self) -> bool:
        return self.state == "connected"

    def log(self, message: str, level: str = "info") -> None:
        entry = LogEntry(level, message)
        self.history.append(entry)
        self.logged.emit(entry)

    def clear_log(self) -> None:
        self.history.clear()

    def _set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self.state_changed.emit(state)

    def _background(self, work: Callable, on_ok: Callable, on_err: Callable) -> None:
        def task():
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 — the engine raises a generic Exception
                self._done.emit(lambda: on_err(exc))
            else:
                self._done.emit(lambda: on_ok(result))
        self._run(task)

    # ── connection ──────────────────────────────────────────────────────────────
    def connect_discord(self, app_id: str) -> bool:
        app_id = app_id.strip()
        if not app_id.isdigit():
            self.failed.emit(tr("ctrl.invalid_app_id.title"), tr("ctrl.invalid_app_id.text"))
            return False
        if self.state != "disconnected":
            return False
        self._set_state("connecting")
        self.log(tr("ctrl.connecting", app_id=app_id))
        ipc = self._ipc_factory(app_id)

        def ok(path):
            self.ipc, self.socket_path = ipc, path
            self.log(tr("ctrl.connected_via", path=path), "ok")
            self._set_state("connected")

        def err(exc):
            self.ipc = None
            self.log(str(exc), "err")
            self._set_state("disconnected")
            self.failed.emit(tr("ctrl.connection_error"), str(exc))

        self._background(ipc.connect, ok, err)
        return True

    def disconnect_discord(self) -> None:
        if self.ipc:
            try:
                self.ipc.disconnect()
            except Exception:  # noqa: BLE001
                pass
        was_connected = self.state != "disconnected"
        self.ipc = None
        self.start_ts = None
        self.active_presence = None
        self.socket_path = ""
        if was_connected:
            self.log(tr("ctrl.disconnected"), "warn")
        self._set_state("disconnected")

    # ── presence ─────────────────────────────────────────────────────────────
    def apply(self, presence: Presence) -> bool:
        if not self.connected or not self.ipc:
            self.failed.emit(tr("ctrl.no_connection.title"), tr("ctrl.no_connection.text"))
            return False
        if presence.show_elapsed and not self.start_ts:
            self.start_ts = int(time.time())
        activity = presence.build_activity(self.start_ts)
        self.log(tr("ctrl.sending"))
        ipc = self.ipc

        def ok(_):
            self.active_presence = presence
            self.log(tr("ctrl.applied"), "ok")
            self.applied.emit()

        def err(exc):
            self.log(tr("ctrl.error", error=exc), "err")
            self.failed.emit(tr("ctrl.apply_failed"), str(exc))
            self.disconnect_discord()

        self._background(lambda: ipc.set_activity(activity), ok, err)
        return True

    def clear(self) -> bool:
        if not self.connected or not self.ipc:
            return False
        self.start_ts = None
        ipc = self.ipc

        def ok(_):
            self.active_presence = None
            self.log(tr("ctrl.removed"), "warn")
            self.cleared.emit()

        def err(exc):
            self.log(tr("ctrl.error", error=exc), "err")
            self.failed.emit(tr("ctrl.clear_failed"), str(exc))

        self._background(ipc.clear_activity, ok, err)
        return True

    def shutdown(self) -> None:
        """Removes the presence and closes the socket (called on exit)."""
        if self.ipc:
            try:
                self.ipc.clear_activity()
                self.ipc.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self.ipc = None
