"""Presence editor: connection, fields and live preview."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..core.models import Presence
from ..i18n import tr
from ..widgets import (ActivityPreview, Button, Card, FormGrid, StatusPill, Suggestion,
                       SuggestionList, TextField, icon)
from ..widgets.status import state_label
from .base import Page

# Field placeholders and labels are catalog keys, re-read on every language change.
PLACEHOLDER_KEYS = {
    "app_id": "presence.ph.app_id", "details": "presence.ph.details", "state": "presence.ph.state",
    "large_key": "presence.ph.key", "small_key": "presence.ph.key",
    "large_text": "presence.ph.hover_text", "small_text": "presence.ph.hover_text",
    "btn1_label": "presence.ph.label", "btn2_label": "presence.ph.label",
    "party_id": "presence.ph.auto",
}
LABEL_KEYS = {
    "details": "presence.field.details", "state": "presence.field.state",
    "large_key": "presence.field.large", "large_text": "presence.field.hint",
    "small_key": "presence.field.small", "small_text": "presence.field.hint",
    "btn1_label": "presence.field.button1", "btn1_url": "presence.field.url",
    "btn2_label": "presence.field.button2", "btn2_url": "presence.field.url",
    "party_size": "presence.field.size", "party_max": "presence.field.max",
    "party_id": "presence.field.id",
}


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
        self._forms: list[FormGrid] = []
        self._cards: list[tuple[Card, str, str]] = []  # (card, title key, subtitle key)

        # ── contextual actions (top bar) ───────────────────────────────
        self.btn_save = Button("", "document-save", on_click=self.save_requested.emit)
        self.btn_clear = Button("", "edit-clear-all", on_click=self.clear_presence)
        self.btn_apply = Button("", "media-playback-start", "primary", on_click=self.apply_presence)

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
        self.preview_title = QLabel(objectName="CardTitle")
        side.addWidget(self.preview_title)
        self.preview = ActivityPreview()
        self.preview.setFixedWidth(300)
        side.addWidget(self.preview)
        self.preview_hint = QLabel(objectName="CardSubtitle")
        self.preview_hint.setWordWrap(True)
        self.preview_hint.setFixedWidth(300)
        side.addWidget(self.preview_hint)
        side.addStretch(1)
        root.addLayout(side)

        for f in self.fields.values():
            f.textChanged.connect(self._on_edit)
        self.show_elapsed.toggled.connect(self._on_edit)
        self.controller.state_changed.connect(self._on_state)
        self.controller.applied.connect(self._on_applied)
        self.controller.cleared.connect(self._refresh)

        self.fields["app_id"].setText(ctx.settings.last_app_id)
        self.retranslate()
        self._on_state(self.controller.state)
        self._refresh()

    # ── construction ───────────────────────────────────────────────────────────
    def _field(self, key, placeholder="", numeric=False):
        f = TextField(placeholder, numeric=numeric)
        f.setObjectName(f"field_{key}")
        self.fields[key] = f
        return f

    def _card(self, title_key: str, subtitle_key: str = "") -> Card:
        card = Card()
        self._cards.append((card, title_key, subtitle_key))
        return card

    def _form(self, columns: int = 1) -> FormGrid:
        form = FormGrid(columns=columns)
        self._forms.append(form)
        return form

    def _connection_card(self):
        card = self._card("presence.conn.title", "presence.conn.subtitle")
        self.status_pill = card.add_action(StatusPill())
        row = QHBoxLayout()
        row.setSpacing(8)
        app_id = self._field("app_id", numeric=True)
        app_id.returnPressed.connect(self._on_app_id_return)
        row.addWidget(app_id, 1)
        # Saved presets, shown when clicking the field (↓ also opens it).
        self.preset_suggestions = SuggestionList(app_id)
        self.preset_suggestions.picked.connect(self.load_preset)
        self.ctx.presets.changed.connect(self._reload_suggestions)
        self._reload_suggestions()
        self.btn_connect = Button("", "network-connect", "primary", on_click=self.toggle_connection)
        self.btn_connect.setMinimumWidth(130)
        row.addWidget(self.btn_connect)
        card.add(row)
        self.socket_label = QLabel(objectName="FieldHint")
        self.socket_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card.add(self.socket_label)
        return card

    def _text_card(self):
        card = self._card("presence.text.title", "presence.text.subtitle")
        form = self._form()
        form.add_field("details", "", self._field("details"))
        form.add_field("state", "", self._field("state"))
        self.show_elapsed = QCheckBox()
        self.show_elapsed.setChecked(True)
        form.add_field("show_elapsed", "", self.show_elapsed)
        card.add(form)
        return card

    def _images_card(self):
        card = self._card("presence.images.title", "presence.images.subtitle")
        form = self._form(columns=2)
        form.add_field("large_key", "", self._field("large_key"))
        form.add_field("large_text", "", self._field("large_text"))
        form.add_field("small_key", "", self._field("small_key"))
        form.add_field("small_text", "", self._field("small_text"))
        card.add(form)
        return card

    def _buttons_card(self):
        card = self._card("presence.buttons.title", "presence.buttons.subtitle")
        form = self._form(columns=2)
        form.add_field("btn1_label", "", self._field("btn1_label"))
        form.add_field("btn1_url", "", self._field("btn1_url", "https://…"))
        form.add_field("btn2_label", "", self._field("btn2_label"))
        form.add_field("btn2_url", "", self._field("btn2_url", "https://…"))
        card.add(form)
        return card

    def _party_card(self):
        card = self._card("presence.party.title", "presence.party.subtitle")
        form = self._form(columns=3)
        form.add_field("party_size", "", self._field("party_size", "1", numeric=True))
        form.add_field("party_max", "", self._field("party_max", "4", numeric=True))
        form.add_field("party_id", "", self._field("party_id"))
        card.add(form)
        return card

    # ── language ───────────────────────────────────────────────────────────────
    def retranslate(self) -> None:
        self.btn_save.setText(tr("presence.btn_save"))
        self.btn_save.setToolTip(tr("presence.tip_save"))
        self.btn_clear.setText(tr("presence.btn_clear"))
        self.btn_clear.setToolTip(tr("presence.tip_clear"))
        self.btn_apply.setText(tr("presence.btn_apply"))
        self.btn_apply.setToolTip(tr("presence.tip_apply"))
        for card, title_key, subtitle_key in self._cards:
            card.set_text(tr(title_key), tr(subtitle_key) if subtitle_key else "")
        for form in self._forms:
            for key, label in form.labels.items():
                if key in LABEL_KEYS:
                    label.setText(tr(LABEL_KEYS[key]))
        for key, placeholder_key in PLACEHOLDER_KEYS.items():
            self.fields[key].setPlaceholderText(tr(placeholder_key))
        self.show_elapsed.setText(tr("presence.show_elapsed"))
        self.preview_title.setText(tr("presence.preview_title"))
        self.preview_hint.setText(tr("presence.preview_hint"))
        self.preview.retranslate()
        self._reload_suggestions()  # the rows carry the "No text" fallback in the current language
        self._on_state(self.controller.state)
        self._refresh()

    # ── Page API ─────────────────────────────────────────────────────────────
    def subtitle(self) -> str:
        if self.controller.active_presence is not None:
            return tr("presence.sub.dirty") if self._dirty else tr("presence.sub.active")
        return {"connected": tr("presence.sub.connected"),
                "connecting": tr("presence.sub.connecting")}.get(
            self.controller.state, tr("presence.sub.disconnected"))

    def header_actions(self):
        return [self.btn_save, self.btn_clear, self.btn_apply]

    # ── data ────────────────────────────────────────────────────────────────
    def presence(self) -> Presence:
        p = Presence(**{k: f.text() for k, f in self.fields.items()})
        p.show_elapsed = self.show_elapsed.isChecked()
        return p

    def set_presence(self, p: Presence) -> None:
        for k, f in self.fields.items():
            if k == "app_id" and self.controller.state != "disconnected":
                continue  # does not change the ID while connected
            f.setText(getattr(p, k))
        self.show_elapsed.setChecked(p.show_elapsed)
        self._mark_invalid([])
        self._refresh()

    # ── presets in the App ID field ───────────────────────────────────────
    def _reload_suggestions(self) -> None:
        items = []
        for name in self.ctx.presets.names():
            p = self.ctx.presets.get(name)
            text = " · ".join(x for x in (p.details, p.state) if x) or tr("presets.meta_empty")
            items.append(Suggestion(key=name, title=name, subtitle=text, value=p.app_id,
                                    trailing=p.app_id, search=f"{p.details} {p.state}"))
        self.preset_suggestions.set_suggestions(items)

    def load_preset(self, name: str) -> bool:
        """Fills the editor with the ``name`` preset and tells the user."""
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
        # Enter that picked a list item must not also connect.
        if not self.preset_suggestions.owns_return():
            self.toggle_connection()

    # ── actions ────────────────────────────────────────────────────────────────
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
            self.ctx.notify(tr("notify.check_fields"),
                            "\n".join(message for _, message in problems), "err")
            return
        self.controller.apply(p)

    def clear_presence(self) -> None:
        self.controller.clear()

    # ── reactions ──────────────────────────────────────────────────────────────
    _VALIDATED_FIELDS = ("app_id", "btn1_label", "btn1_url", "btn2_label", "btn2_url",
                         "party_size", "party_max")

    def _mark_invalid(self, problems) -> None:
        """Highlight the fields named by each problem; the tooltip lists every message."""
        joined = " ".join(message for _, message in problems)
        bad = {name for names, _ in problems for name in names}
        for key in self._VALIDATED_FIELDS:
            is_bad = key in bad
            self.fields[key].set_invalid(is_bad, joined if is_bad else "")

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
        self.btn_connect.setText({"connected": tr("presence.btn_disconnect"),
                                  "connecting": state_label("connecting")}.get(
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
