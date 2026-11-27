"""Editor da presença: conexão, campos e pré-visualização ao vivo."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..core.models import Presence
from ..i18n import tr
from ..widgets import (ActivityPreview, Button, Card, FormGrid, StatusPill, Suggestion,
                       SuggestionList, TextField, icon)
from ..widgets.status import state_label
from .base import Page


class PresencePage(Page):
    key = "presence"
    title_key = "page.presence.title"
    icon = "im-user-online"

    save_requested = Signal()

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.controller = ctx.controller
        self._dirty = False
        self.fields: dict[str, TextField] = {}

        # ── ações contextuais (barra superior) ───────────────────────────────
        self.btn_save = Button(tr("presence.btn_save"), "document-save", tooltip=tr("presence.tip_save"),
                               on_click=self.save_requested.emit)
        self.btn_clear = Button(tr("presence.btn_clear"), "edit-clear-all", tooltip=tr("presence.tip_clear"),
                                on_click=self.clear_presence)
        self.btn_apply = Button(tr("presence.btn_apply"), "media-playback-start", "primary",
                                tooltip=tr("presence.tip_apply"), on_click=self.apply_presence)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        col = QVBoxLayout(content)
        col.setContentsMargins(24, 20, 12, 24)
        col.setSpacing(16)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        col.addWidget(self._connection_card())
        col.addWidget(self._text_card())
        col.addWidget(self._images_card())
        col.addWidget(self._buttons_card())
        col.addWidget(self._party_card())
        col.addStretch(1)

        side = QVBoxLayout()
        side.setContentsMargins(12, 20, 24, 24)
        side.setSpacing(10)
        side.addWidget(QLabel(tr("presence.preview_title"), objectName="CardTitle"))
        self.preview = ActivityPreview()
        self.preview.setFixedWidth(300)
        side.addWidget(self.preview)
        hint = QLabel(tr("presence.preview_hint"), objectName="CardSubtitle")
        hint.setWordWrap(True)
        hint.setFixedWidth(300)
        side.addWidget(hint)
        side.addStretch(1)
        root.addLayout(side)

        for f in self.fields.values():
            f.textChanged.connect(self._on_edit)
        self.show_elapsed.toggled.connect(self._on_edit)
        self.controller.state_changed.connect(self._on_state)
        self.controller.applied.connect(self._on_applied)
        self.controller.cleared.connect(self._refresh)

        self.fields["app_id"].setText(ctx.settings.last_app_id)
        self._on_state(self.controller.state)
        self._refresh()

    # ── construção ───────────────────────────────────────────────────────────
    def _field(self, key, placeholder="", numeric=False):
        f = TextField(placeholder, numeric=numeric)
        f.setObjectName(f"field_{key}")
        self.fields[key] = f
        return f

    def _connection_card(self):
        card = Card(tr("presence.conn.title"), tr("presence.conn.subtitle"))
        self.status_pill = card.add_action(StatusPill())
        row = QHBoxLayout()
        row.setSpacing(8)
        app_id = self._field("app_id", tr("presence.ph.app_id"), numeric=True)
        app_id.returnPressed.connect(self._on_app_id_return)
        row.addWidget(app_id, 1)
        # Lista das predefinições salvas ao clicar no campo (↓ também abre).
        self.preset_suggestions = SuggestionList(app_id)
        self.preset_suggestions.picked.connect(self.load_preset)
        self.ctx.presets.changed.connect(self._reload_suggestions)
        self._reload_suggestions()
        self.btn_connect = Button(tr("presence.btn_connect"), "network-connect", "primary",
                                  on_click=self.toggle_connection)
        self.btn_connect.setMinimumWidth(130)
        row.addWidget(self.btn_connect)
        card.add(row)
        self.socket_label = QLabel(objectName="FieldHint")
        self.socket_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card.add(self.socket_label)
        return card

    def _text_card(self):
        card = Card(tr("presence.text.title"), tr("presence.text.subtitle"))
        form = FormGrid()
        form.add_field("details", tr("presence.field.details"),
                       self._field("details", tr("presence.ph.details")))
        form.add_field("state", tr("presence.field.state"),
                       self._field("state", tr("presence.ph.state")))
        self.show_elapsed = QCheckBox(tr("presence.show_elapsed"))
        self.show_elapsed.setChecked(True)
        form.add_field("show_elapsed", "", self.show_elapsed)
        card.add(form)
        return card

    def _images_card(self):
        card = Card(tr("presence.images.title"), tr("presence.images.subtitle"))
        form = FormGrid(columns=2)
        form.add_field("large_key", tr("presence.field.large"), self._field("large_key", tr("presence.ph.key")))
        form.add_field("large_text", tr("presence.field.hint"),
                       self._field("large_text", tr("presence.ph.hover_text")))
        form.add_field("small_key", tr("presence.field.small"), self._field("small_key", tr("presence.ph.key")))
        form.add_field("small_text", tr("presence.field.hint"),
                       self._field("small_text", tr("presence.ph.hover_text")))
        card.add(form)
        return card

    def _buttons_card(self):
        card = Card(tr("presence.buttons.title"), tr("presence.buttons.subtitle"))
        form = FormGrid(columns=2)
        form.add_field("btn1_label", tr("presence.field.button1"),
                       self._field("btn1_label", tr("presence.ph.label")))
        form.add_field("btn1_url", tr("presence.field.url"), self._field("btn1_url", "https://…"))
        form.add_field("btn2_label", tr("presence.field.button2"),
                       self._field("btn2_label", tr("presence.ph.label")))
        form.add_field("btn2_url", tr("presence.field.url"), self._field("btn2_url", "https://…"))
        card.add(form)
        return card

    def _party_card(self):
        card = Card(tr("presence.party.title"), tr("presence.party.subtitle"))
        form = FormGrid(columns=3)
        form.add_field("party_size", tr("presence.field.size"), self._field("party_size", "1", numeric=True))
        form.add_field("party_max", tr("presence.field.max"), self._field("party_max", "4", numeric=True))
        form.add_field("party_id", tr("presence.field.id"), self._field("party_id", tr("presence.ph.auto")))
        card.add(form)
        return card

    # ── Page API ─────────────────────────────────────────────────────────────
    def subtitle(self) -> str:
        if self.controller.active_presence is not None:
            return tr("presence.sub.dirty") if self._dirty else tr("presence.sub.active")
        return {"connected": tr("presence.sub.connected"),
                "connecting": tr("presence.sub.connecting")}.get(
            self.controller.state, tr("presence.sub.disconnected"))

    def header_actions(self):
        return [self.btn_save, self.btn_clear, self.btn_apply]

    # ── dados ────────────────────────────────────────────────────────────────
    def presence(self) -> Presence:
        p = Presence(**{k: f.text() for k, f in self.fields.items()})
        p.show_elapsed = self.show_elapsed.isChecked()
        return p

    def set_presence(self, p: Presence) -> None:
        for k, f in self.fields.items():
            if k == "app_id" and self.controller.state != "disconnected":
                continue  # não troca o ID com a conexão aberta
            f.setText(getattr(p, k))
        self.show_elapsed.setChecked(p.show_elapsed)
        self._mark_invalid([])
        self._refresh()

    # ── predefinições no campo App ID ───────────────────────────────────────
    def _reload_suggestions(self) -> None:
        items = []
        for name in self.ctx.presets.names():
            p = self.ctx.presets.get(name)
            text = " · ".join(x for x in (p.details, p.state) if x) or tr("presets.meta_empty")
            items.append(Suggestion(key=name, title=name, subtitle=text, value=p.app_id,
                                    trailing=p.app_id, search=f"{p.details} {p.state}"))
        self.preset_suggestions.set_suggestions(items)

    def load_preset(self, name: str) -> bool:
        """Preenche o editor com a predefinição ``name`` e avisa o usuário."""
        presence = self.ctx.presets.get(name)
        if presence is None:
            return False
        self.set_presence(presence)
        self.controller.log(tr("presence.loaded_log", name=name), "ok")
        note = tr("presence.note.review")
        if self.controller.state != "disconnected" and presence.app_id and \
                presence.app_id != self.fields["app_id"].text():
            note = tr("presence.note.app_id")
        elif self.controller.state == "disconnected":
            note = tr("presence.note.connect")
        self.ctx.notify(tr("presence.loaded_title", name=name), note, "info")
        return True

    def _on_app_id_return(self) -> None:
        # Enter que escolheu um item da lista não deve também conectar.
        if not self.preset_suggestions.owns_return():
            self.toggle_connection()

    # ── ações ────────────────────────────────────────────────────────────────
    def toggle_connection(self) -> None:
        if self.controller.state == "disconnected":
            app_id = self.fields["app_id"].text().strip()
            if self.controller.connect_discord(app_id):
                self.ctx.settings.last_app_id = app_id
        else:
            self.controller.disconnect_discord()

    def apply_presence(self) -> None:
        p = self.presence()
        problems = p.validate()
        self._mark_invalid(problems)
        if problems:
            self.ctx.notify(tr("notify.check_fields"), "\n".join(problems), "err")
            return
        self.controller.apply(p)

    def clear_presence(self) -> None:
        self.controller.clear()

    # ── reações ──────────────────────────────────────────────────────────────
    def _mark_invalid(self, problems) -> None:
        joined = " ".join(problems)
        checks = {
            "app_id": "Application ID" in joined,
            "btn1_label": "Botão 1" in joined, "btn1_url": "Botão 1" in joined,
            "btn2_label": "Botão 2" in joined, "btn2_url": "Botão 2" in joined,
            "party_size": "Party" in joined, "party_max": "Party" in joined,
        }
        for key, bad in checks.items():
            self.fields[key].set_invalid(bad, joined if bad else "")

    def _on_edit(self, *_):
        if self.controller.active_presence is not None:
            self._dirty = True
        self._refresh()

    def _on_applied(self):
        self._dirty = False
        self._refresh()

    def _on_state(self, state: str):
        connected = state == "connected"
        self.status_pill.set_state(state)
        self.fields["app_id"].setEnabled(state == "disconnected")
        self.btn_connect.setText(
            {"connected": tr("presence.btn_disconnect"), "connecting": state_label("connecting")}.get(
                state, tr("presence.btn_connect")))
        self.btn_connect.setIcon(icon(
            "network-disconnect" if connected else "network-connect"))
        self.btn_connect.set_variant("default" if connected else "primary")
        self.btn_connect.setEnabled(state != "connecting")
        self.btn_apply.setEnabled(connected)
        self.btn_clear.setEnabled(connected)
        self.socket_label.setText(tr("presence.socket", path=self.controller.socket_path) if connected else "")
        self.socket_label.setVisible(connected)
        if state == "disconnected":
            self._dirty = False
        self._refresh()

    def _refresh(self, *_):
        self.preview.update_from(self.presence(), self.controller.start_ts)
        self.header_changed.emit()
