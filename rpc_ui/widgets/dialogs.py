"""Dialogs with the application look and a service that the tests can replace."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from ..i18n import tr
from .buttons import Button
from .icons import icon as theme_icon


class _BaseDialog(QDialog):
    def __init__(self, title: str, text: str = "", icon: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(420)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 18)
        outer.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(14)
        if icon:
            ic = QLabel()
            ic.setPixmap(theme_icon(icon).pixmap(QSize(40, 40)))
            ic.setAlignment(Qt.AlignTop)
            top.addWidget(ic)
        texts = QVBoxLayout()
        texts.setSpacing(6)
        texts.addWidget(QLabel(title, objectName="DialogTitle"))
        self.text_label = QLabel(text, objectName="DialogText")
        self.text_label.setWordWrap(True)
        self.text_label.setVisible(bool(text))
        texts.addWidget(self.text_label)
        self.content = QVBoxLayout()
        self.content.setSpacing(6)
        texts.addLayout(self.content)
        top.addLayout(texts, 1)
        outer.addLayout(top)

        self.buttons = QHBoxLayout()
        self.buttons.addStretch(1)
        outer.addLayout(self.buttons)

    def _add_buttons(self, ok_text: str, ok_variant: str, cancel_text: str | None = None):
        self.cancel_button = Button(cancel_text or tr("common.cancel"), on_click=self.reject)
        self.ok_button = Button(ok_text, variant=ok_variant, on_click=self.accept)
        self.ok_button.setDefault(True)
        self.buttons.addWidget(self.cancel_button)
        self.buttons.addWidget(self.ok_button)


class ConfirmDialog(_BaseDialog):
    def __init__(self, title: str, text: str, confirm_text: str | None = None,
                 destructive: bool = False, parent=None):
        super().__init__(title, text, "dialog-warning" if destructive else "dialog-information", parent)
        self._add_buttons(confirm_text or tr("common.confirm"), "danger" if destructive else "primary")


class TextInputDialog(_BaseDialog):
    """Asks for a text; ``validate`` returns an error message or ``None``."""

    def __init__(self, title: str, label: str, value: str = "", confirm_text: str | None = None,
                 validate: Callable[[str], str | None] | None = None, parent=None):
        super().__init__(title, label, None, parent)
        self._validate = validate
        self.field = QLineEdit(value)
        self.field.setClearButtonEnabled(True)
        self.field.selectAll()
        self.error_label = QLabel(objectName="DialogError")
        self.error_label.hide()
        self.content.addWidget(self.field)
        self.content.addWidget(self.error_label)
        self._add_buttons(confirm_text or tr("common.save"), "primary")
        self.field.textChanged.connect(self._revalidate)
        self._revalidate()

    def value(self) -> str:
        return self.field.text().strip()

    def _revalidate(self) -> None:
        text = self.value()
        error = None if text else ""
        if text and self._validate:
            error = self._validate(text)
        self.ok_button.setEnabled(error is None)
        self.error_label.setText(error or "")
        self.error_label.setVisible(bool(error))

    def accept(self) -> None:
        if self.ok_button.isEnabled():
            super().accept()


class DialogService:
    """Single entry point for opening modal dialogs; the tests replace this class."""

    def __init__(self, parent: QWidget | None = None):
        self.parent = parent

    def ask_text(self, title: str, label: str, value: str = "", confirm_text: str | None = None,
                 validate=None) -> str | None:
        dlg = TextInputDialog(title, label, value, confirm_text, validate, self.parent)
        return dlg.value() if dlg.exec() == QDialog.Accepted else None

    def confirm(self, title: str, text: str, confirm_text: str | None = None,
                destructive: bool = False) -> bool:
        dlg = ConfirmDialog(title, text, confirm_text, destructive, self.parent)
        return dlg.exec() == QDialog.Accepted
