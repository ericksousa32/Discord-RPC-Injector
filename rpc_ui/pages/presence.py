"""Editor da presença: conexão, campos e pré-visualização ao vivo."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..core.models import Presence
from ..widgets import (ActivityPreview, Button, Card, FormGrid, StatusPill, Suggestion,
                       SuggestionList, TextField, icon)
from .base import Page


class PresencePage(Page):
    key = "presence"
    title = "Presença"
    icon = "im-user-online"

    save_requested = Signal()

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.controller = ctx.controller
        self._dirty = False
        self.fields: dict[str, TextField] = {}

        # ── ações contextuais (barra superior) ───────────────────────────────
        self.btn_save = Button("Salvar predefinição", "document-save", tooltip="Salvar campos como predefinição (Ctrl+S)",
                               on_click=self.save_requested.emit)
        self.btn_clear = Button("Limpar", "edit-clear-all", tooltip="Remover a presença do Discord",
                                on_click=self.clear_presence)
        self.btn_apply = Button("Aplicar", "media-playback-start", "primary",
                                tooltip="Enviar presença ao Discord (Ctrl+Enter)", on_click=self.apply_presence)

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
        side.addWidget(QLabel("Pré-visualização", objectName="CardTitle"))
        self.preview = ActivityPreview()
        self.preview.setFixedWidth(300)
        side.addWidget(self.preview)
        hint = QLabel("Aproximação de como o cartão aparece no seu perfil do Discord.",
                      objectName="CardSubtitle")
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
        card = Card("Conexão", "Informe o Application ID do Discord Developer Portal "
                               "ou clique no campo para usar uma predefinição.")
        self.status_pill = card.add_action(StatusPill())
        row = QHBoxLayout()
        row.setSpacing(8)
        app_id = self._field("app_id", "ex.: 123456789012345678", numeric=True)
        app_id.returnPressed.connect(self._on_app_id_return)
        row.addWidget(app_id, 1)
        # Lista das predefinições salvas ao clicar no campo (↓ também abre).
        self.preset_suggestions = SuggestionList(app_id)
        self.preset_suggestions.picked.connect(self.load_preset)
        self.ctx.presets.changed.connect(self._reload_suggestions)
        self._reload_suggestions()
        self.btn_connect = Button("Conectar", "network-connect", "primary", on_click=self.toggle_connection)
        self.btn_connect.setMinimumWidth(130)
        row.addWidget(self.btn_connect)
        card.add(row)
        self.socket_label = QLabel(objectName="FieldHint")
        self.socket_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card.add(self.socket_label)
        return card

    def _text_card(self):
        card = Card("Texto", "As duas linhas exibidas abaixo do nome do aplicativo.")
        form = FormGrid()
        form.add_field("details", "Detalhes", self._field("details", "O que você está fazendo"))
        form.add_field("state", "Estado", self._field("state", "Informação complementar"))
        self.show_elapsed = QCheckBox("Mostrar tempo decorrido")
        self.show_elapsed.setChecked(True)
        form.add_field("show_elapsed", "", self.show_elapsed)
        card.add(form)
        return card

    def _images_card(self):
        card = Card("Imagens", "Chaves dos assets enviados em Rich Presence → Art Assets.")
        form = FormGrid(columns=2)
        form.add_field("large_key", "Grande", self._field("large_key", "chave"))
        form.add_field("large_text", "Dica", self._field("large_text", "texto ao passar o mouse"))
        form.add_field("small_key", "Pequena", self._field("small_key", "chave"))
        form.add_field("small_text", "Dica", self._field("small_text", "texto ao passar o mouse"))
        card.add(form)
        return card

    def _buttons_card(self):
        card = Card("Botões", "Até dois links públicos. Rótulo e URL são obrigatórios juntos.")
        form = FormGrid(columns=2)
        form.add_field("btn1_label", "Botão 1", self._field("btn1_label", "rótulo"))
        form.add_field("btn1_url", "URL", self._field("btn1_url", "https://…"))
        form.add_field("btn2_label", "Botão 2", self._field("btn2_label", "rótulo"))
        form.add_field("btn2_url", "URL", self._field("btn2_url", "https://…"))
        card.add(form)
        return card

    def _party_card(self):
        card = Card("Grupo (party)", "Exibe “x de y” ao lado do estado.")
        form = FormGrid(columns=3)
        form.add_field("party_size", "Tamanho", self._field("party_size", "1", numeric=True))
        form.add_field("party_max", "Máximo", self._field("party_max", "4", numeric=True))
        form.add_field("party_id", "ID", self._field("party_id", "automático"))
        card.add(form)
        return card

    # ── Page API ─────────────────────────────────────────────────────────────
    def subtitle(self) -> str:
        if self.controller.active_presence is not None:
            return "Alterações não aplicadas" if self._dirty else "Presença ativa no Discord"
        return {"connected": "Conectado — pronto para aplicar",
                "connecting": "Conectando ao Discord…"}.get(self.controller.state, "Não conectado ao Discord")

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
            text = " · ".join(x for x in (p.details, p.state) if x) or "Sem texto"
            items.append(Suggestion(key=name, title=name, subtitle=text, value=p.app_id,
                                    trailing=p.app_id, search=f"{p.details} {p.state}"))
        self.preset_suggestions.set_suggestions(items)

    def load_preset(self, name: str) -> bool:
        """Preenche o editor com a predefinição ``name`` e avisa o usuário."""
        presence = self.ctx.presets.get(name)
        if presence is None:
            return False
        self.set_presence(presence)
        self.controller.log(f'"{name}" carregada.', "ok")
        note = "Revise os campos e clique em Aplicar."
        if self.controller.state != "disconnected" and presence.app_id and \
                presence.app_id != self.fields["app_id"].text():
            note = "O Application ID só muda após desconectar."
        elif self.controller.state == "disconnected":
            note = "Clique em Conectar e depois em Aplicar."
        self.ctx.notify(f'"{name}" carregada', note, "info")
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
            self.ctx.notify("Verifique os campos", "\n".join(problems), "err")
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
        self.btn_connect.setText({"connected": "Desconectar", "connecting": "Conectando…"}.get(state, "Conectar"))
        self.btn_connect.setIcon(icon(
            "network-disconnect" if connected else "network-connect"))
        self.btn_connect.set_variant("default" if connected else "primary")
        self.btn_connect.setEnabled(state != "connecting")
        self.btn_apply.setEnabled(connected)
        self.btn_clear.setEnabled(connected)
        self.socket_label.setText(f"Socket: {self.controller.socket_path}" if connected else "")
        self.socket_label.setVisible(connected)
        if state == "disconnected":
            self._dirty = False
        self._refresh()

    def _refresh(self, *_):
        self.preview.update_from(self.presence(), self.controller.start_ts)
        self.header_changed.emit()
