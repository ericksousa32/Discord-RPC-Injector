"""Event log with text/level filtering and an empty state."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QStackedWidget, QVBoxLayout, QWidget)

from ..i18n import tr
from ..widgets import Button, EmptyState, icon
from ..widgets.lists import clear_list
from .base import Page

LEVEL_ICONS = {"ok": "dialog-ok", "err": "dialog-error", "warn": "dialog-warning", "info": "dialog-information"}
# (label key, filtered level)
LEVEL_FILTERS = [("log.level.all", None), ("log.level.ok", "ok"), ("log.level.warn", "warn"),
                 ("log.level.err", "err"), ("log.level.info", "info")]


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
    title_key = "page.log.title"
    icon = "view-history"

    @property
    def search_placeholder(self) -> str:
        return tr("log.search")

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.controller = ctx.controller
        self._filter = ""

        self.level = QComboBox()
        for _label_key, value in LEVEL_FILTERS:
            self.level.addItem("", value)
        self.level.currentIndexChanged.connect(lambda *_: self.reload())
        self.btn_clear = Button("", "edit-clear-all", on_click=self.clear)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 24)
        self.stack = QStackedWidget()
        self.list = QListWidget()
        self.list.setObjectName("LogList")
        self.empty = EmptyState("view-history", "", "")
        self.no_results = EmptyState("edit-find", "")
        for w in (self.list, self.empty, self.no_results):
            self.stack.addWidget(w)
        lay.addWidget(self.stack)

        self.controller.logged.connect(self._on_logged)
        self.retranslate()

    # ── idioma ───────────────────────────────────────────────────────────────
    def retranslate(self) -> None:
        for i, (label_key, _value) in enumerate(LEVEL_FILTERS):
            self.level.setItemText(i, tr(label_key))
        self.btn_clear.setText(tr("log.btn_clear"))
        self.empty.set_text(tr("log.empty.title"), tr("log.empty.text"))
        self.no_results.set_text(tr("log.no_results.title"))
        self.reload()
        self.header_changed.emit()

    def subtitle(self) -> str:
        n = len(self.controller.history)
        errs = sum(1 for e in self.controller.history if e.level == "err")
        if n == 0:
            base = tr("log.count_zero")
        else:
            base = tr("log.count_one" if n == 1 else "log.count_many", n=n)
        if errs:
            errors = tr("log.errors_one" if errs == 1 else "log.errors_many", n=errs)
            base = tr("log.with_errors", events=base, errors=errors)
        return base

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
        item.setSizeHint(row.sizeHint() + QSize(0, 6))  # item margin in the QSS
        self.list.addItem(item)
        self.list.setItemWidget(item, row)

    def _on_logged(self, entry) -> None:
        if self._matches(entry):
            self._append(entry)
            self.list.scrollToBottom()
        self._update_stack()

    def reload(self) -> None:
        clear_list(self.list)
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
