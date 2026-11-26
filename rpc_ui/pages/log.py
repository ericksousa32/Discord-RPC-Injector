"""Registro de eventos com filtro por texto/nível e estado vazio."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QStackedWidget, QVBoxLayout, QWidget)

from ..widgets import Button, EmptyState, icon
from .base import Page

LEVEL_ICONS = {"ok": "dialog-ok", "err": "dialog-error", "warn": "dialog-warning", "info": "dialog-information"}
LEVEL_FILTERS = [("Todos os níveis", None), ("Sucesso", "ok"), ("Avisos", "warn"),
                 ("Erros", "err"), ("Informações", "info")]


class LogRow(QWidget):
    def __init__(self, entry, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(icon(LEVEL_ICONS.get(entry.level, "dialog-information")).pixmap(QSize(16, 16)))
        lay.addWidget(ic)
        lay.addWidget(QLabel(entry.time.strftime("%H:%M:%S"), objectName="LogTime"))
        msg = QLabel(entry.message, objectName="LogMessage")
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(msg, 1)


class LogPage(Page):
    key = "log"
    title = "Registro"
    icon = "view-history"
    search_placeholder = "Filtrar registro…"

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.controller = ctx.controller
        self._filter = ""

        self.level = QComboBox()
        for text, value in LEVEL_FILTERS:
            self.level.addItem(text, value)
        self.level.currentIndexChanged.connect(lambda *_: self.reload())
        self.btn_clear = Button("Limpar registro", "edit-clear-all", on_click=self.clear)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 24)
        self.stack = QStackedWidget()
        self.list = QListWidget()
        self.list.setObjectName("LogList")
        self.empty = EmptyState("view-history", "Nada registrado ainda",
                                "Conexões, envios de presença e erros aparecerão aqui.")
        self.no_results = EmptyState("edit-find", "Nenhum evento corresponde ao filtro")
        for w in (self.list, self.empty, self.no_results):
            self.stack.addWidget(w)
        lay.addWidget(self.stack)

        self.controller.logged.connect(self._on_logged)
        self.reload()

    def subtitle(self) -> str:
        n = len(self.controller.history)
        errs = sum(1 for e in self.controller.history if e.level == "err")
        base = "Sem eventos" if n == 0 else f"{n} evento" + ("s" if n != 1 else "")
        return base + (f" · {errs} erro" + ("s" if errs != 1 else "") if errs else "")

    def header_actions(self):
        return [self.level, self.btn_clear]

    def set_filter(self, text: str) -> None:
        self._filter = text.strip().casefold()
        self.reload()

    def _matches(self, entry) -> bool:
        lvl = self.level.currentData()
        if lvl and entry.level != lvl:
            return False
        return not self._filter or self._filter in entry.message.casefold()

    def _append(self, entry) -> None:
        item = QListWidgetItem()
        row = LogRow(entry)
        item.setSizeHint(row.sizeHint() + QSize(0, 6))  # margem do item no QSS
        self.list.addItem(item)
        self.list.setItemWidget(item, row)

    def _on_logged(self, entry) -> None:
        if self._matches(entry):
            self._append(entry)
            self.list.scrollToBottom()
        self._update_stack()

    def reload(self) -> None:
        self.list.clear()
        for e in self.controller.history:
            if self._matches(e):
                self._append(e)
        self.list.scrollToBottom()
        self._update_stack()

    def _update_stack(self) -> None:
        if not self.controller.history:
            self.stack.setCurrentWidget(self.empty)
        elif self.list.count() == 0:
            self.stack.setCurrentWidget(self.no_results)
        else:
            self.stack.setCurrentWidget(self.list)
        self.btn_clear.setEnabled(bool(self.controller.history))
        self.header_changed.emit()

    def clear(self) -> None:
        self.controller.clear_log()
        self.reload()
