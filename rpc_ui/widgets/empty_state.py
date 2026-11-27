from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .buttons import Button
from .icons import icon as theme_icon


class EmptyState(QWidget):
    """Centered message (Kirigami PlaceholderMessage style) with an optional action."""

    def __init__(self, icon: str, title: str, text: str = "", action_text: str | None = None,
                 action_icon: str | None = None, on_action=None, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(10)
        self.icon_label = QLabel(alignment=Qt.AlignCenter)
        self.icon_label.setPixmap(theme_icon(icon).pixmap(QSize(64, 64), QIcon.Mode.Disabled))
        self.title_label = QLabel(title, objectName="EmptyTitle", alignment=Qt.AlignCenter)
        self.text_label = QLabel(text, objectName="EmptyText", alignment=Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setMaximumWidth(380)
        self.text_label.setVisible(bool(text))
        lay.addWidget(self.icon_label)
        lay.addWidget(self.title_label)
        lay.addWidget(self.text_label, 0, Qt.AlignHCenter)
        self.action_button = None
        if action_text:
            self.action_button = Button(action_text, action_icon, "primary", on_click=on_action)
            lay.addSpacing(6)
            lay.addWidget(self.action_button, 0, Qt.AlignHCenter)

    def set_text(self, title: str, text: str = "") -> None:
        self.title_label.setText(title)
        self.text_label.setText(text)
        self.text_label.setVisible(bool(text))
