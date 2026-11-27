"""Services shared between the pages (injected, which makes testing easier)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core.controller import PresenceController
from .core.presets import PresetStore
from .core.settings import AppSettings


@dataclass
class AppContext:
    controller: PresenceController
    presets: PresetStore
    settings: AppSettings
    theme: Any = None        # ThemeManager
    dialogs: Any = None      # DialogService (definido pela janela)
    toasts: Any = None       # ToastHost (definido pela janela)

    def notify(self, title: str, text: str = "", tone: str = "info", **kw):
        if self.toasts is not None:
            return self.toasts.show(title, text, tone, **kw)
        return None
