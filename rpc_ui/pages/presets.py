"""Lista de predefinições com busca, estados vazios e desfazer exclusão."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..core.models import Presence
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
        meta = " · ".join(x for x in (p.details, p.state) if x) or "Sem texto"
        texts.addWidget(QLabel(meta, objectName="PresetRowMeta"))
        lay.addLayout(texts, 1)
        app = QLabel(f"App ID {p.app_id}" if p.app_id else "", objectName="PresetRowMeta")
        lay.addWidget(app)


class PresetsPage(Page):
    key = "presets"
    title = "Predefinições"
    icon = "bookmarks"
    search_placeholder = "Buscar predefinições…"

    load_requested = Signal(str, object)     # nome, Presence
    create_requested = Signal()

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.store = ctx.presets
        self._filter = ""

        self.btn_new = Button("Nova a partir da atual", "document-new", on_click=self.create_requested.emit)
        self.btn_rename = Button("Renomear", "edit-rename", on_click=self.rename_selected)
        self.btn_delete = Button("Excluir", "edit-delete", "danger", on_click=self.delete_selected)
        self.btn_load = Button("Carregar", "document-open", "primary", on_click=self.load_selected)

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
        self.empty = EmptyState("bookmarks", "Nenhuma predefinição",
                                "Salve a presença atual para reutilizá-la depois com um clique.",
                                "Salvar presença atual", "document-save", self.create_requested.emit)
        self.no_results = EmptyState("edit-find", "Nada encontrado",
                                     "Nenhuma predefinição corresponde à busca.")
        for w in (self.list, self.empty, self.no_results):
            self.stack.addWidget(w)

        self.store.changed.connect(self.reload)
        self.reload()

    # ── Page API ─────────────────────────────────────────────────────────────
    def subtitle(self) -> str:
        n = len(self.store)
        return "Nenhuma salva" if n == 0 else f"{n} salva" + ("s" if n != 1 else "")

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
                return "Já existe uma predefinição com esse nome."
            return None
        return check

    def save_new(self, presence: Presence) -> str | None:
        suggestion = presence.details.strip() or "Nova predefinição"
        name = self.ctx.dialogs.ask_text("Salvar predefinição", "Dê um nome para identificar esta presença.",
                                         suggestion, "Salvar")
        if not name:
            return None
        if name in self.store and not self.ctx.dialogs.confirm(
                "Substituir predefinição?", f'Já existe "{name}". Deseja substituí-la?', "Substituir"):
            return None
        self.store.put(name, presence)
        self.select(name)
        self.ctx.controller.log(f'"{name}" salva.', "ok")
        self.ctx.notify("Predefinição salva", f'"{name}" foi adicionada à lista.', "ok")
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
        new = self.ctx.dialogs.ask_text("Renomear predefinição", f'Novo nome para "{old}":', old,
                                        "Renomear", self._name_error(old))
        if not new or new == old:
            return
        self.store.rename(old, new)
        self.select(new)
        self.ctx.controller.log(f'Renomeado "{old}" → "{new}".', "ok")
        self.ctx.notify("Predefinição renomeada", f'"{old}" agora se chama "{new}".', "ok")

    def delete_selected(self) -> None:
        name = self.selected_name()
        if not name:
            return
        if not self.ctx.dialogs.confirm("Excluir predefinição?",
                                        f'"{name}" será removida da lista.', "Excluir", destructive=True):
            return
        backup = self.store.get(name)
        self.store.delete(name)
        self.ctx.controller.log(f'"{name}" excluída.', "warn")

        def undo():
            if name not in self.store:
                self.store.put(name, backup)
                self.select(name)
                self.ctx.controller.log(f'Exclusão de "{name}" desfeita.', "info")

        self.ctx.notify("Predefinição excluída", f'"{name}" foi removida.', "warn",
                        action="Desfazer", on_action=undo, timeout_ms=7000)
