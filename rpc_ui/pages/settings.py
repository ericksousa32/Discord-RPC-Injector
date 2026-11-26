"""Preferências: tema (sistema/KDE, claro, escuro), bandeja e informações."""

from __future__ import annotations

from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QRadioButton,
                               QScrollArea, QSystemTrayIcon, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..core import engine
from ..widgets import Card
from .base import Page

THEME_OPTIONS = [("system", "Sistema", "Segue o esquema de cores e a cor de destaque do KDE Plasma"),
                 ("light", "Claro", "Sempre claro"),
                 ("dark", "Escuro", "Sempre escuro")]


class SettingsPage(Page):
    key = "settings"
    title = "Configurações"
    icon = "configure"

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        settings = ctx.settings

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        col = QVBoxLayout(content)
        col.setContentsMargins(24, 20, 24, 24)
        col.setSpacing(16)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # ── aparência ────────────────────────────────────────────────────────
        appearance = Card("Aparência", "Escolha o tema da interface.")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.theme_group = QButtonGroup(self)
        self.theme_buttons: dict[str, QRadioButton] = {}
        for key, text, tip in THEME_OPTIONS:
            rb = QRadioButton(text, objectName="ThemeOption")
            rb.setToolTip(tip)
            rb.setChecked(settings.theme == key)
            rb.toggled.connect(lambda on, k=key: on and self._set_theme(k))
            self.theme_group.addButton(rb)
            self.theme_buttons[key] = rb
            row.addWidget(rb, 1)
        appearance.add(row)
        self.theme_hint = QLabel(objectName="FieldHint")
        self.theme_hint.setWordWrap(True)
        appearance.add(self.theme_hint)
        col.addWidget(appearance)

        # ── comportamento ────────────────────────────────────────────────────
        behavior = Card("Comportamento")
        self.close_to_tray = QCheckBox("Manter na bandeja do sistema ao fechar a janela")
        self.close_to_tray.setChecked(settings.close_to_tray)
        self.close_to_tray.toggled.connect(lambda v: setattr(settings, "close_to_tray", v))
        tray_ok = QSystemTrayIcon.isSystemTrayAvailable()
        self.close_to_tray.setEnabled(tray_ok)
        behavior.add(self.close_to_tray)
        if not tray_ok:
            behavior.add(QLabel("Nenhuma bandeja do sistema disponível nesta sessão.", objectName="FieldHint"))
        col.addWidget(behavior)

        # ── sobre ────────────────────────────────────────────────────────────
        about = Card("Sobre")
        info = QLabel(
            f"<b>{APP_NAME}</b> {__version__}<br>"
            "Injeta Rich Presence no Discord (incluindo Flatpak) via socket IPC.<br>"
            f"<span>Predefinições: {engine.PRESETS_FILE}</span>",
            objectName="CardSubtitle")
        info.setWordWrap(True)
        about.add(info)
        col.addWidget(about)
        col.addStretch(1)

        self._update_hint()

    def _set_theme(self, key: str) -> None:
        self.ctx.settings.theme = key
        if self.ctx.theme is not None:
            self.ctx.theme.set_mode(key)
        self._update_hint()

    def _update_hint(self) -> None:
        mode = self.ctx.settings.theme
        if mode == "system":
            source = {"kde": "esquema do KDE Plasma", "qt": "paleta do Qt"}.get(
                getattr(self.ctx.theme, "source", ""), "sistema")
            self.theme_hint.setText(f"Usando as cores do {source}. Mudanças no tema do "
                                    "Plasma são aplicadas automaticamente.")
        else:
            self.theme_hint.setText("Tema fixo, independente do sistema.")

    def subtitle(self) -> str:
        return "Aparência e comportamento"
