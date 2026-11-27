"""UI preferences persisted with QSettings."""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal

THEMES = ("system", "light", "dark")


class AppSettings(QObject):
    changed = Signal(str)

    DEFAULTS = {"theme": "system", "close_to_tray": True, "last_app_id": ""}

    def __init__(self, path: str | None = None, parent=None):
        super().__init__(parent)
        if path:
            self._qs = QSettings(path, QSettings.IniFormat)
        else:
            self._qs = QSettings("DiscordRPCInjector", "DiscordRPCInjector")

    def _get(self, key):
        default = self.DEFAULTS[key]
        value = self._qs.value(key, default)
        if isinstance(default, bool):
            return value if isinstance(value, bool) else str(value).lower() == "true"
        return str(value)

    def _set(self, key, value):
        if self._get(key) == value:
            return
        self._qs.setValue(key, value)
        self._qs.sync()
        self.changed.emit(key)

    @property
    def theme(self) -> str:
        t = self._get("theme")
        return t if t in THEMES else "system"

    @theme.setter
    def theme(self, value: str):
        if value not in THEMES:
            raise ValueError(value)
        self._set("theme", value)

    @property
    def close_to_tray(self) -> bool:
        return self._get("close_to_tray")

    @close_to_tray.setter
    def close_to_tray(self, value: bool):
        self._set("close_to_tray", bool(value))

    @property
    def last_app_id(self) -> str:
        return self._get("last_app_id")

    @last_app_id.setter
    def last_app_id(self, value: str):
        self._set("last_app_id", value)
