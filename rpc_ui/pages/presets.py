"""Lista de predefinições com busca, estados vazios e desfazer exclusão."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..core.models import Presence
from ..i18n import tr
from ..widgets import Button, EmptyState, icon
from .base import Page


class PresetRow(QWidget):
    def __init__(self, name: str, p: Presence, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        ic = QLabel()
        ic.setPixmap(icon("bookmarks").pixmap(QSize(28, 28)))
        lay.addWidget(ic)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(QLabel(name, objectName="PresetRowTitle"))
        meta = " · ".join(x for x in (p.details, p.state) if x) or tr("presets.meta_empty")
        texts.addWidget(QLabel(meta, objectName="PresetRowMeta"))
        lay.addLayout(texts, 1)
        app = QLabel(tr("presets.app_id", app_id=p.app_id) if p.app_id else "", objectName="PresetRowMeta")
        lay.addWidget(app)


class PresetsPage(Page):
    key = "presets"
    title_key = "page.presets.title"
    icon = "bookmarks"

    load_requested = Signal(str, object)     # nome, Presence
    create_requested = Signal()

    @property
    def search_placeholder(self) -> str:
        return tr("presets.search")

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.store = ctx.presets
        self._filter = ""

        self.btn_new = Button(tr("presets.btn_new"), "document-new", on_click=self.create_requested.emit)
        self.btn_rename = Button(tr("presets.btn_rename"), "edit-rename", on_click=self.rename_selected)
        self.btn_delete = Button(tr("presets.btn_delete"), "edit-delete", "danger", on_click=self.delete_selected)
        self.btn_load = Button(tr("presets.btn_load"), "document-open", "primary", on_click=self.load_selected)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 16, 24, 24)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)

        self.list = QListWidget()
        self.list.setObjectName("PresetList")
        self.list.setSpacing(0)
        self.list.setUniformItemSizes(True)
        self.list.itemDoubleClicked.connect(lambda *_: self.load_selected())
        self.list.itemSelectionChanged.connect(self._update_actions)
        self.empty = EmptyState("bookmarks", tr("presets.empty.title"), tr("presets.empty.text"),
                                tr("presets.empty.action"), "document-save", self.create_requested.emit)
        self.no_results = EmptyState("edit-find", tr("presets.no_results.title"),
                                     tr("presets.no_results.text"))
        for w in (self.list, self.empty, self.no_results):
            self.stack.addWidget(w)

        self.store.changed.connect(self.reload)
        self.reload()

    # ── Page API ─────────────────────────────────────────────────────────────
    def subtitle(self) -> str:
        n = len(self.store)
        if n == 0:
            return tr("presets.count_zero")
        return tr("presets.count_one" if n == 1 else "presets.count_many", n=n)

    def header_actions(self):
        return [self.btn_new, self.btn_rename, self.btn_delete, self.btn_load]

    def set_filter(self, text: str) -> None:
        self._filter = text.strip().casefold()
        self.reload()

    # ── lista ────────────────────────────────────────────────────────────────
    def _matches(self, name: str, p: Presence) -> bool:
        if not self._filter:
            return True
        hay = " ".join((name, p.details, p.state, p.app_id)).casefold()
        return all(tok in hay for tok in self._filter.split())

    def visible_names(self) -> list[str]:
        return [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]

    def reload(self) -> None:
        selected = self.selected_name()
        self.list.clear()
        for name in self.store.names():
            p = self.store.get(name)
            if not self._matches(name, p):
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, name)
            row = PresetRow(name, p)
            item.setSizeHint(row.sizeHint() + QSize(0, 6))  # margem do item no QSS
            self.list.addItem(item)
            self.list.setItemWidget(item, row)
            if name == selected:
                item.setSelected(True)
        if len(self.store) == 0:
            self.stack.setCurrentWidget(self.empty)
        elif self.list.count() == 0:
            self.stack.setCurrentWidget(self.no_results)
        else:
            self.stack.setCurrentWidget(self.list)
            if not self.list.selectedItems():
                self.list.setCurrentRow(0)
        self._update_actions()
        self.header_changed.emit()

    def select(self, name: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == name:
                self.list.setCurrentRow(i)
                return

    def selected_name(self) -> str | None:
        items = self.list.selectedItems() if hasattr(self, "list") else []
        return items[0].data(Qt.UserRole) if items else None

    def _update_actions(self) -> None:
        has = self.selected_name() is not None
        for b in (self.btn_rename, self.btn_delete, self.btn_load):
            b.setEnabled(has)

    # ── ações ────────────────────────────────────────────────────────────────
    def _name_error(self, current: str | None = None):
        def check(text: str):
            if text != current and text in self.store:
                return tr("presets.name_exists")
            return None
        return check

    def save_new(self, presence: Presence) -> str | None:
        suggestion = presence.details.strip() or tr("presets.name_default")
        name = self.ctx.dialogs.ask_text(tr("presets.save.title"), tr("presets.save.label"),
                                         suggestion, tr("common.save"))
        if not name:
            return None
        if name in self.store and not self.ctx.dialogs.confirm(
                tr("presets.replace.title"), tr("presets.replace.text", name=name),
                tr("presets.replace.confirm")):
            return None
        self.store.put(name, presence)
        self.select(name)
        self.ctx.controller.log(tr("presets.log_saved", name=name), "ok")
        self.ctx.notify(tr("presets.saved.title"), tr("presets.saved.text", name=name), "ok")
        return name

    def load_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        self.load_requested.emit(name, self.store.get(name))

    def rename_selected(self) -> None:
        old = self.selected_name()
        if not old:
            return
        new = self.ctx.dialogs.ask_text(tr("presets.rename.title"), tr("presets.rename.label", name=old),
                                        old, tr("presets.rename.confirm"), self._name_error(old))
        if not new or new == old:
            return
        self.store.rename(old, new)
        self.select(new)
        self.ctx.controller.log(tr("presets.log_renamed", old=old, new=new), "ok")
        self.ctx.notify(tr("presets.renamed.title"), tr("presets.renamed.text", old=old, new=new), "ok")

    def delete_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        if not self.ctx.dialogs.confirm(tr("presets.delete.title"),
                                        tr("presets.delete.text", name=name),
                                        tr("presets.delete.confirm"), destructive=True):
            return
        backup = self.store.get(name)
        self.store.delete(name)
        self.ctx.controller.log(tr("presets.log_deleted", name=name), "warn")

        def undo():
            if name not in self.store:
                self.store.put(name, backup)
                self.select(name)
                self.ctx.controller.log(tr("presets.log_undone", name=name), "info")

        self.ctx.notify(tr("presets.deleted.title"), tr("presets.deleted.text", name=name), "warn",
                        action=tr("presets.undo"), on_action=undo, timeout_ms=7000)
