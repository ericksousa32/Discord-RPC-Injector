from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Separator")


class Card(QFrame):
    """Surface with an optional title, subtitle and actions on the right."""

    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 18)
        outer.setSpacing(12)

        self.header = QWidget()
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(0, 0, 0, 0)
        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.title_label = QLabel(title, objectName="CardTitle")
        self.subtitle_label = QLabel(subtitle, objectName="CardSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        hl.addLayout(titles, 1)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(6)
        hl.addLayout(self.actions_layout)
        self.header.setVisible(bool(title))
        outer.addWidget(self.header)

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        outer.addLayout(self.body)

    def add_action(self, widget: QWidget) -> QWidget:
        self.actions_layout.addWidget(widget, 0, Qt.AlignTop)
        return widget

    def add(self, item) -> None:
        if isinstance(item, QWidget):
            self.body.addWidget(item)
        else:
            self.body.addLayout(item)
