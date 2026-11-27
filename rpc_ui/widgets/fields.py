from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QWidget

from .style import set_prop


class TextField(QLineEdit):
    """QLineEdit with a placeholder, a clear button and error marking."""

    def __init__(self, placeholder: str = "", numeric: bool = False, max_length: int = 128,
                 parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMaxLength(max_length)
        if numeric:
            self.setValidator(QIntValidator(0, 2_000_000_000, self))

    def set_invalid(self, invalid: bool, message: str = "") -> None:
        set_prop(self, "invalid", "true" if invalid else "false")
        self.setToolTip(message if invalid else "")


class FormGrid(QWidget):
    """Grid form in the Kirigami FormLayout style: label on the right, field on the left.

    ``columns`` places label/field pairs side by side on wide screens.
    """

    edited = Signal()

    def __init__(self, columns: int = 1, parent=None):
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(10)
        self._columns = columns
        self._index = 0
        self.fields: dict[str, QWidget] = {}
        self.labels: dict[str, QLabel] = {}  # label of each field (for switching the language)
        for c in range(columns):
            self._grid.setColumnStretch(c * 2 + 1, 1)

    def add_field(self, key: str, label: str, widget: QWidget, span: int = 1,
                  hint: str | None = None) -> QWidget:
        if span > 1 and self._index % self._columns:
            self._index += self._columns - self._index % self._columns
        row, col = divmod(self._index, self._columns)
        lbl = QLabel(label, objectName="FieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setBuddy(widget)
        self._grid.addWidget(lbl, row * 2, col * 2)
        self._grid.addWidget(widget, row * 2, col * 2 + 1, 1, span * 2 - 1)
        if hint:
            h = QLabel(hint, objectName="FieldHint")
            h.setWordWrap(True)
            self._grid.addWidget(h, row * 2 + 1, col * 2 + 1, 1, span * 2 - 1)
        self._index += span if span > 1 else 1
        self.fields[key] = widget
        self.labels[key] = lbl
        if isinstance(widget, QLineEdit):
            widget.textEdited.connect(self.edited)
        return widget
