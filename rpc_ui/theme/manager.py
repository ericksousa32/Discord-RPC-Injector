"""Applies the theme and follows system/KDE theme changes in real time."""

from __future__ import annotations

import os

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .palette import Tokens, builtin_tokens, kde_tokens, kdeglobals_path, system_tokens
from .stylesheet import build_stylesheet


def _palette_from(t: Tokens) -> QPalette:
    p = QPalette()
    roles = {
        QPalette.Window: t.window, QPalette.WindowText: t.text, QPalette.Base: t.surface_alt,
        QPalette.AlternateBase: t.surface, QPalette.Text: t.text, QPalette.Button: t.surface,
        QPalette.ButtonText: t.text, QPalette.Highlight: t.accent,
        QPalette.HighlightedText: t.on_accent, QPalette.ToolTipBase: t.surface,
        QPalette.ToolTipText: t.text, QPalette.PlaceholderText: t.text_faint,
        QPalette.Link: t.accent, QPalette.Mid: t.border, QPalette.Midlight: t.hover,
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, QColor(t.text_faint))
    return p


class ThemeManager(QObject):
    """``mode``: ``system`` (follows KDE), ``light`` or ``dark``."""

    changed = Signal(object)  # Tokens

    def __init__(self, app: QApplication, mode: str = "system", kdeglobals: str | None = None):
        super().__init__(app)
        self._app = app
        self._mode = mode
        self._kdeglobals = kdeglobals or kdeglobals_path()
        self.tokens: Tokens = builtin_tokens("light")
        # Keep the platform palette before overwriting it with ours.
        self._platform_palette = QPalette(app.palette())

        # Debounce: KDE rewrites kdeglobals several times when the theme changes.
        self._debounce = QTimer(self, singleShot=True, interval=250)
        self._debounce.timeout.connect(self._on_system_change)
        self._watcher = QFileSystemWatcher(self)
        if os.path.exists(self._kdeglobals):
            self._watcher.addPath(self._kdeglobals)
        self._watcher.fileChanged.connect(lambda *_: self._debounce.start())
        app.styleHints().colorSchemeChanged.connect(lambda *_: self._debounce.start())
        self.apply()

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode != self._mode:
            self._mode = mode
            self.apply()

    def _on_system_change(self) -> None:
        # The file may be replaced (new inode): start watching it again.
        if os.path.exists(self._kdeglobals) and self._kdeglobals not in self._watcher.files():
            self._watcher.addPath(self._kdeglobals)
        if self._mode == "system":
            self.apply()

    def apply(self) -> None:
        if self._mode == "system":
            self.tokens = system_tokens(self._kdeglobals, self._platform_palette)
            self.source = "kde" if kde_tokens(self._kdeglobals) is not None else "qt"
        else:
            self.tokens = builtin_tokens(self._mode)
            self.source = "builtin"
        self._app.setPalette(_palette_from(self.tokens))
        self._app.setStyleSheet(build_stylesheet(self.tokens))
        self.changed.emit(self.tokens)
