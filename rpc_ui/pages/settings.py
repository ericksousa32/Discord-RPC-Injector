"""Preferences: theme (system/KDE, light, dark), tray and information."""

from __future__ import annotations

from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QRadioButton,
                               QScrollArea, QSystemTrayIcon, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__
from ..core import engine
from ..i18n import tr
from ..widgets import Card
from .base import Page

# (saved value, label key, hint key)
THEME_OPTIONS = [("system", "theme.system", "theme.system.tip"),
                 ("light", "theme.light", "theme.light.tip"),
                 ("dark", "theme.dark", "theme.dark.tip")]


class SettingsPage(Page):
    key = "settings"
    title_key = "page.settings.title"
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

        # ── appearance ────────────────────────────────────────────────────────
        appearance = Card(tr("settings.appearance.title"), tr("settings.appearance.subtitle"))
        row = QHBoxLayout()
        row.setSpacing(10)
        self.theme_group = QButtonGroup(self)
        self.theme_buttons: dict[str, QRadioButton] = {}
        for key, label_key, tip_key in THEME_OPTIONS:
            rb = QRadioButton(tr(label_key), objectName="ThemeOption")
            rb.setToolTip(tr(tip_key))
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

        # ── behavior ────────────────────────────────────────────────────
        behavior = Card(tr("settings.behavior.title"))
        self.close_to_tray = QCheckBox(tr("settings.close_to_tray"))
        self.close_to_tray.setChecked(settings.close_to_tray)
        self.close_to_tray.toggled.connect(lambda v: setattr(settings, "close_to_tray", v))
        tray_ok = QSystemTrayIcon.isSystemTrayAvailable()
        self.close_to_tray.setEnabled(tray_ok)
        behavior.add(self.close_to_tray)
        if not tray_ok:
            behavior.add(QLabel(tr("settings.no_tray"), objectName="FieldHint"))
        col.addWidget(behavior)

        # ── about ────────────────────────────────────────────────────────────
        about = Card(tr("settings.about.title"))
        info = QLabel(
            f"<b>{APP_NAME}</b> {__version__}<br>"
            f"{tr('settings.about.text')}<br>"
            f"<span>{tr('settings.presets_path', path=engine.PRESETS_FILE)}</span>",
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
            source = {"kde": tr("theme.source.kde"), "qt": tr("theme.source.qt")}.get(
                getattr(self.ctx.theme, "source", ""), tr("theme.source.default"))
            self.theme_hint.setText(tr("settings.theme_system_hint", source=source))
        else:
            self.theme_hint.setText(tr("settings.theme_fixed_hint"))

    def subtitle(self) -> str:
        return tr("settings.subtitle")
