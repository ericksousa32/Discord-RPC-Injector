from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from .icons import icon


class PageHeader(QWidget):
    """Top bar: page title/subtitle, search and contextual actions."""

    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PageHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 14, 18, 14)
        lay.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_label = QLabel(objectName="PageTitle")
        self.subtitle_label = QLabel(objectName="PageSubtitle")
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        lay.addLayout(titles, 1)

        self.search = QLineEdit(objectName="SearchField")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icon("edit-find"), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self.search_changed)
        self.search.hide()
        lay.addWidget(self.search)

        self._actions_host = QWidget()
        self._actions = QHBoxLayout(self._actions_host)
        self._actions.setContentsMargins(0, 0, 0, 0)
        self._actions.setSpacing(6)
        lay.addWidget(self._actions_host)

    def set_page(self, title: str, subtitle: str = "", actions=(), search_placeholder=None,
                 search_text: str = "") -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))

        # Buttons belong to the pages: here they are only re-attached.
        while self._actions.count():
            w = self._actions.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.setParent(None)
        for w in actions:
            self._actions.addWidget(w)
            w.show()

        self.search.blockSignals(True)
        self.search.setText(search_text)
        self.search.blockSignals(False)
        self.search.setPlaceholderText(search_placeholder or "")
        self.search.setVisible(search_placeholder is not None)

    def action_widgets(self) -> list[QWidget]:
        return [self._actions.itemAt(i).widget() for i in range(self._actions.count())]
