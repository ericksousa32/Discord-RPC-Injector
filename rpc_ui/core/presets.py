"""Preset store on top of the engine functions."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Signal

from ..i18n import tr
from .models import Presence


class PresetStore(QObject):
    changed = Signal()

    def __init__(self, load: Callable[[], dict] | None = None,
                 save: Callable[[dict], None] | None = None, parent=None):
        super().__init__(parent)
        if load is None or save is None:
            from . import engine
            load = load or engine.load_presets
            save = save or engine.save_presets
        self._load, self._save = load, save
        self._data: dict = dict(load() or {})

    def names(self) -> list[str]:
        return sorted(self._data, key=str.casefold)

    def __contains__(self, name: str) -> bool:
        return name in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, name: str) -> Presence | None:
        raw = self._data.get(name)
        return Presence.from_dict(raw) if raw is not None else None

    def put(self, name: str, presence: Presence) -> None:
        self._data[name] = presence.to_dict()
        self._commit()

    def rename(self, old: str, new: str) -> None:
        if old not in self._data:
            raise KeyError(old)
        if new in self._data and new != old:
            raise ValueError(tr("presets.store_exists", name=new))
        self._data[new] = self._data.pop(old)
        self._commit()

    def delete(self, name: str) -> None:
        self._data.pop(name, None)
        self._commit()

    def _commit(self) -> None:
        self._save(self._data)
        self.changed.emit()
