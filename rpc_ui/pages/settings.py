"""Preferences: language, theme (system/KDE, light, dark), tray and information."""

from __future__ import annotations

from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel,
                               QRadioButton, QScrollArea, QSystemTrayIcon, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..core import engine
from ..core.settings import LANGUAGES
from ..i18n import tr
from ..widgets import Card, FormGrid
from .base import Page

# (saved value, label key, hint key)
THEME_OPTIONS = [("system", "theme.system", "theme.system.tip"),
                 ("light", "theme.light", "theme.light.tip"),
                 ("dark", "theme.dark", "theme.dark.tip")]

# Language names are written in each language, so they are not translated.
LANGUAGE_NAMES = {"en": "English", "pt_BR": "Português (Brasil)"}


class SettingsPage(Page):
    key = "settings"
    title_key = "page.settings.title"
    icon = "configure"

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        settings = ctx.settings
        self._cards: list[tuple[Card, str, str]] = []  # (card, title key, subtitle key)

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

        # ── language ───────────────────────────────────────────────────────────
        language = self._card("settings.language.title", "settings.language.subtitle")
        self.language = QComboBox()
        for code in LANGUAGES:
            self.language.addItem(LANGUAGE_NAMES.get(code, code), code)
        self.language.setCurrentIndex(max(0, self.language.findData(settings.language)))
        self.language.currentIndexChanged.connect(self._on_language_picked)
        self.language_form = FormGrid()
        self.language_form.add_field("language", "", self.language)
        language.add(self.language_form)
        col.addWidget(language)

        # ── appearance ────────────────────────────────────────────────────────
        appearance = self._card("settings.appearance.title", "settings.appearance.subtitle")
        row = QHBoxLayout()
        row.setSpacing(10)
        self.theme_group = QButtonGroup(self)
        self.theme_buttons: dict[str, QRadioButton] = {}
        self._theme_texts: list[tuple[QRadioButton, str, str]] = []
        for key, label_key, tip_key in THEME_OPTIONS:
            rb = QRadioButton(objectName="ThemeOption")
            rb.setChecked(settings.theme == key)
            rb.toggled.connect(lambda on, k=key: on and self._set_theme(k))
            self.theme_group.addButton(rb)
            self.theme_buttons[key] = rb
            self._theme_texts.append((rb, label_key, tip_key))
            row.addWidget(rb, 1)
        appearance.add(row)
        self.theme_hint = QLabel(objectName="FieldHint")
        self.theme_hint.setWordWrap(True)
        appearance.add(self.theme_hint)
        col.addWidget(appearance)

        # ── behavior ────────────────────────────────────────────────────
        behavior = self._card("settings.behavior.title")
        self.close_to_tray = QCheckBox()
        self.close_to_tray.setChecked(settings.close_to_tray)
        self.close_to_tray.toggled.connect(lambda v: setattr(settings, "close_to_tray", v))
        tray_ok = QSystemTrayIcon.isSystemTrayAvailable()
        self.close_to_tray.setEnabled(tray_ok)
        behavior.add(self.close_to_tray)
        self.no_tray = QLabel(objectName="FieldHint")
        self.no_tray.setVisible(not tray_ok)
        behavior.add(self.no_tray)
        col.addWidget(behavior)

        # ── about ────────────────────────────────────────────────────────────
        about = self._card("settings.about.title")
        self.about_info = QLabel(objectName="CardSubtitle")
        self.about_info.setWordWrap(True)
        about.add(self.about_info)
        col.addWidget(about)
        col.addStretch(1)

        self.retranslate()

    def _card(self, title_key: str, subtitle_key: str = "") -> Card:
        card = Card()
        self._cards.append((card, title_key, subtitle_key))
        return card

    # ── language ───────────────────────────────────────────────────────────────
    def retranslate(self) -> None:
        for card, title_key, subtitle_key in self._cards:
            card.set_text(tr(title_key), tr(subtitle_key) if subtitle_key else "")
        self.language_form.labels["language"].setText(tr("settings.language.field"))
        for rb, label_key, tip_key in self._theme_texts:
            rb.setText(tr(label_key))
            rb.setToolTip(tr(tip_key))
        self.close_to_tray.setText(tr("settings.close_to_tray"))
        self.no_tray.setText(tr("settings.no_tray"))
        self.about_info.setText(
            f"<b>{APP_NAME}</b> {__version__}<br>"
            f"{tr('settings.about.text')}<br>"
            f"<span>{tr('settings.presets_path', path=engine.PRESETS_FILE)}</span>")
        self._update_hint()

    def _on_language_picked(self, index: int) -> None:
        code = self.language.itemData(index)
        if code:
            # AppSettings emits ``changed``; the window applies the language and retranslates.
            self.ctx.settings.language = code

    def _set_theme(self, key: str) -> None:
        self.ctx.settings.theme = key
        if self.ctx.theme is not None:
            self.ctx.theme.set_mode(key)
        self._update_hint()

    def _update_hint(self) -> None:
        mode = self.ctx.settings.theme
        if mode == "system":
            source = {"kde": tr("theme.source.kde"), "qt": tr("theme.source.qt")}.get(
                getattr(self.ctx.theme, "source", ""), tr("theme.source.default"))
            self.theme_hint.setText(tr("settings.theme_system_hint", source=source))
        else:
            self.theme_hint.setText(tr("settings.theme_fixed_hint"))

    def subtitle(self) -> str:
        return tr("settings.subtitle")
