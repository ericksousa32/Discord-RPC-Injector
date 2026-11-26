"""Ícones do tema (Breeze no KDE) com fallback desenhado para outros ambientes."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

# nome freedesktop → glifo de fallback
_FALLBACK = {
    "user-online": "●", "im-user-online": "●",
    "document-save": "⤓", "document-save-as": "⤓", "edit-clear": "⌫", "edit-clear-all": "⌫",
    "media-playback-start": "▶", "edit-rename": "✎", "edit-delete": "🗑", "document-open": "⤒",
    "network-connect": "⇄", "network-disconnect": "⨯", "view-list-details": "☰",
    "bookmarks": "★", "view-history": "⟲", "configure": "⚙", "settings-configure": "⚙",
    "edit-find": "⌕", "dialog-information": "ℹ", "dialog-ok-apply": "✓", "dialog-ok": "✓",
    "dialog-error": "✕", "dialog-warning": "!", "window-close": "✕", "list-add": "+",
    "document-new": "+", "help-about": "ℹ", "edit-copy": "⧉", "view-preview": "◉",
}


def _glyph(char: str, size: int = 32) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    color = QColor("#8a8f98")  # neutro: legível em temas claros e escuros
    p.setPen(color)
    f = QFont()
    f.setPixelSize(int(size * 0.7))
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, char)
    p.end()
    return QIcon(pm)


def icon(name: str) -> QIcon:
    ic = QIcon.fromTheme(name)
    if not ic.isNull():
        return ic
    return _glyph(_FALLBACK.get(name, "•"))
