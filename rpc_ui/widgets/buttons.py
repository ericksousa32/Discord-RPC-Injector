from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton

from .icons import icon as theme_icon
from .style import set_prop


class Button(QPushButton):
    """Button with variants: ``default``, ``primary``, ``danger`` and ``flat``."""

    def __init__(self, text: str = "", icon: str | None = None, variant: str = "default",
                 tooltip: str | None = None, parent=None, on_click=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(16, 16))
        if icon:
            self.setIcon(theme_icon(icon))
        if tooltip:
            self.setToolTip(tooltip)
        self.set_variant(variant)
        if on_click is not None:
            self.clicked.connect(on_click)

    def set_variant(self, variant: str) -> None:
        set_prop(self, "variant", variant)
