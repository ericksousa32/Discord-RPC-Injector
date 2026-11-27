"""Entry point: builds the services, applies the theme and opens the window."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from . import APP_ID, APP_NAME
from .context import AppContext
from .core.controller import PresenceController
from .core.presets import PresetStore
from .core.settings import AppSettings
from .i18n import set_language
from .main_window import MainWindow
from .theme import ThemeManager


def installed_desktop_file(app_id: str = APP_ID) -> bool:
    """Tells whether ``<app_id>.desktop`` is installed in any XDG directory."""
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return any(os.path.isfile(os.path.join(d, "applications", f"{app_id}.desktop"))
               for d in [data_home, *data_dirs.split(":")] if d)


def create_app(argv=None) -> QApplication:
    # Identify with the .desktop file only when it exists; otherwise the portal
    # XDG refuses the registration ("App info not found") and emits a warning.
    if QApplication.instance() is None and installed_desktop_file():
        QApplication.setDesktopFileName(APP_ID)
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # the tray keeps the app alive
    return app


def build_window(app: QApplication, ctx: AppContext | None = None, enable_tray: bool = True,
                 kdeglobals: str | None = None) -> MainWindow:
    if ctx is None:
        ctx = AppContext(PresenceController(), PresetStore(), AppSettings())
    set_language(ctx.settings.language)  # before creating the widgets: they are born translated
    if ctx.theme is None:
        ctx.theme = ThemeManager(app, ctx.settings.theme, kdeglobals)
    return MainWindow(ctx, enable_tray=enable_tray)


def main(argv=None) -> int:
    app = create_app(argv)
    window = build_window(app)
    window.show()
    return app.exec()
