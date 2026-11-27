"""Color tokens: built-in themes (light/dark) and reading the KDE theme."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, replace

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette


@dataclass(frozen=True)
class Tokens:
    name: str
    is_dark: bool
    window: str
    sidebar: str
    surface: str
    surface_alt: str
    hover: str
    border: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    on_accent: str
    success: str = "#27ae60"
    warning: str = "#f67400"
    danger: str = "#da4453"

    def accent_soft(self, alpha: int = 48) -> str:
        c = QColor(self.accent)
        return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"

    def tint(self, color: str, alpha: int) -> str:
        c = QColor(color)
        return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


# Palettes inspired by Breeze, used when the user forces light/dark.
LIGHT = Tokens(
    name="light", is_dark=False,
    window="#f3f4f6", sidebar="#eaecef", surface="#ffffff", surface_alt="#f6f7f9",
    hover="#e3e6ea", border="#d4d8de", text="#1f2328", text_muted="#5c6370",
    text_faint="#8a919c", accent="#3daee9", on_accent="#ffffff",
)
DARK = Tokens(
    name="dark", is_dark=True,
    window="#1b1e21", sidebar="#202326", surface="#272a2f", surface_alt="#2f3338",
    hover="#363a40", border="#3a3f45", text="#e8eaed", text_muted="#a7adb5",
    text_faint="#737a83", accent="#3daee9", on_accent="#ffffff",
    success="#2ecc71", warning="#f39c1f", danger="#ed5565",
)


def builtin_tokens(name: str) -> Tokens:
    return DARK if name == "dark" else LIGHT


# ── KDE ──────────────────────────────────────────────────────────────────────

def kdeglobals_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "kdeglobals")


def _rgb(value: str | None) -> QColor | None:
    if not value:
        return None
    try:
        parts = [int(p) for p in value.split(",")[:3]]
        return QColor(*parts) if len(parts) == 3 else None
    except ValueError:
        return None


def _mix(a: QColor, b: QColor, t: float) -> str:
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    ).name()


def _from_colors(window: QColor, view: QColor, text: QColor, accent: QColor,
                 on_accent: QColor | None, name: str) -> Tokens:
    dark = window.lightness() < 128
    base = DARK if dark else LIGHT
    return replace(
        base, name=name, is_dark=dark,
        window=window.name(),
        sidebar=_mix(window, text, 0.03),
        surface=view.name() if abs(view.lightness() - window.lightness()) < 60 else _mix(window, text, 0.04),
        surface_alt=_mix(window, text, 0.06),
        hover=_mix(window, text, 0.11),
        border=_mix(window, text, 0.17),
        text=text.name(),
        text_muted=_mix(text, window, 0.32),
        text_faint=_mix(text, window, 0.52),
        accent=accent.name(),
        on_accent=(on_accent or (QColor("#ffffff") if accent.lightness() < 170 else QColor("#111111"))).name(),
    )


def kde_tokens(path: str | None = None) -> Tokens | None:
    """Reads the colors of the active Plasma scheme from ``kdeglobals``."""
    path = path or kdeglobals_path()
    if not os.path.exists(path):
        return None
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        cp.read(path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None

    def get(section, key):
        return _rgb(cp.get(section, key, fallback=None))

    window = get("Colors:Window", "BackgroundNormal")
    text = get("Colors:Window", "ForegroundNormal")
    if window is None:
        return None
    if text is None:
        text = QColor("#fcfcfc") if window.lightness() < 128 else QColor("#232629")
    view = get("Colors:View", "BackgroundNormal") or window
    accent = (get("General", "AccentColor") or get("Colors:Selection", "BackgroundNormal")
              or QColor("#3daee9"))
    on_accent = get("Colors:Selection", "ForegroundNormal")
    return _from_colors(window, view, text, accent, on_accent, "system")


def palette_tokens(palette: QPalette | None = None) -> Tokens:
    pal = palette or QGuiApplication.palette()
    return _from_colors(
        pal.color(QPalette.Window), pal.color(QPalette.Base), pal.color(QPalette.WindowText),
        pal.color(QPalette.Highlight), pal.color(QPalette.HighlightedText), "system",
    )


def system_tokens(kdeglobals: str | None = None, palette: QPalette | None = None) -> Tokens:
    """Order: KDE scheme → Qt scheme hint → platform palette."""
    kde = kde_tokens(kdeglobals)
    if kde is not None:
        return kde
    app = QGuiApplication.instance()
    if app is not None:
        scheme = app.styleHints().colorScheme()
        pal_tokens = palette_tokens(palette)
        if scheme == Qt.ColorScheme.Dark and not pal_tokens.is_dark:
            return replace(DARK, name="system", accent=pal_tokens.accent)
        if scheme == Qt.ColorScheme.Light and pal_tokens.is_dark:
            return replace(LIGHT, name="system", accent=pal_tokens.accent)
        return pal_tokens
    return replace(LIGHT, name="system")
