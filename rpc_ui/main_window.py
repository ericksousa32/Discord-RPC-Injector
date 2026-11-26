"""Janela principal: barra lateral + barra superior + páginas empilhadas."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenu, QStackedWidget,
                               QSystemTrayIcon, QVBoxLayout, QWidget)

from . import APP_NAME
from .context import AppContext
from .core import engine
from .pages import LogPage, Page, PresencePage, PresetsPage, SettingsPage
from .widgets import DialogService, PageHeader, Sidebar, StatusPill, ToastHost


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext, enable_tray: bool = True):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(960, 640)
        self.resize(1180, 760)
        # Vetorial: fica nítido na barra de tarefas, no alt+tab e na bandeja.
        for path in (engine.ICON_SVG_PATH, engine.ICON_PATH):
            if os.path.exists(path) and not QIcon(path).isNull():
                self.setWindowIcon(QIcon(path))
                break

        root = QWidget(objectName="AppRoot")
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self.sidebar = Sidebar(APP_NAME, "Rich Presence para Discord", engine.ICON_PATH)
        h.addWidget(self.sidebar)

        main = QWidget()
        v = QVBoxLayout(main)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.header = PageHeader()
        v.addWidget(self.header)
        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)
        h.addWidget(main, 1)

        ctx.dialogs = ctx.dialogs or DialogService(self)
        ctx.toasts = ToastHost(main)

        # ── páginas ──────────────────────────────────────────────────────────
        self.presence_page = PresencePage(ctx)
        self.presets_page = PresetsPage(ctx)
        self.log_page = LogPage(ctx)
        self.settings_page = SettingsPage(ctx)
        self.pages: dict[str, Page] = {}
        self.sidebar.add_section("Geral")
        self._add_page(self.presence_page, "Ctrl+1")
        self._add_page(self.presets_page, "Ctrl+2")
        self._add_page(self.log_page, "Ctrl+3")
        self.sidebar.add_section("Aplicativo")
        self._add_page(self.settings_page, "Ctrl+,")

        self.status = StatusPill()
        self.sidebar.footer.addWidget(self.status, 0, Qt.AlignLeft)

        self._search_text: dict[str, str] = {}
        self.sidebar.current_changed.connect(self.navigate)
        self.header.search_changed.connect(self._on_search)

        # ── ligações entre páginas ───────────────────────────────────────────
        self.presence_page.save_requested.connect(self.save_current_as_preset)
        self.presets_page.create_requested.connect(self.save_current_as_preset)
        self.presets_page.load_requested.connect(self._load_preset)
        ctx.presets.changed.connect(self._update_badges)
        ctx.controller.state_changed.connect(self._on_state)
        ctx.controller.applied.connect(lambda: ctx.notify("Presença atualizada", "O Discord já exibe a nova atividade.", "ok"))
        ctx.controller.cleared.connect(lambda: ctx.notify("Presença removida", tone="warn"))
        ctx.controller.failed.connect(lambda title, msg: ctx.notify(title, msg, "err", timeout_ms=7000))

        self._shortcuts()
        self._update_badges()
        self.navigate("presence")

        self.tray = None
        self._really_quit = False
        if enable_tray and QSystemTrayIcon.isSystemTrayAvailable():
            self._setup_tray()

    # ── navegação ────────────────────────────────────────────────────────────
    def _add_page(self, page: Page, shortcut: str) -> None:
        self.pages[page.key] = page
        self.stack.addWidget(page)
        self.sidebar.add_item(page.key, page.title, page.icon, shortcut)
        page.header_changed.connect(lambda p=page: self._sync_header(p, full=False))

    def current_page(self) -> Page:
        return self.stack.currentWidget()

    def navigate(self, key: str) -> None:
        page = self.pages[key]
        self.sidebar.set_current(key)
        if self.stack.currentWidget() is not page:
            self.stack.setCurrentWidget(page)
        self._sync_header(page, full=True)
        page.activated()

    def _sync_header(self, page: Page, full: bool) -> None:
        if page is not self.stack.currentWidget():
            return
        if full:
            self.header.set_page(page.title, page.subtitle(), page.header_actions(),
                                 page.search_placeholder, self._search_text.get(page.key, ""))
        else:
            self.header.subtitle_label.setText(page.subtitle())
            self.header.subtitle_label.setVisible(bool(page.subtitle()))

    def _on_search(self, text: str) -> None:
        page = self.current_page()
        self._search_text[page.key] = text
        page.set_filter(text)

    def _shortcuts(self) -> None:
        def sc(seq, fn):
            QShortcut(QKeySequence(seq), self, activated=fn)
        sc(QKeySequence.Find, self.focus_search)
        sc("Ctrl+S", self.save_current_as_preset)
        sc("Ctrl+Return", self.presence_page.apply_presence)
        sc(QKeySequence.Quit, self.quit)

    def focus_search(self) -> None:
        if self.current_page().search_placeholder is None:
            self.navigate("presets")
        self.header.search.setFocus()
        self.header.search.selectAll()

    # ── fluxo ────────────────────────────────────────────────────────────────
    def save_current_as_preset(self) -> None:
        self.presets_page.save_new(self.presence_page.presence())

    def _load_preset(self, name: str, presence=None) -> None:
        self.presence_page.load_preset(name)
        self.navigate("presence")

    def _on_state(self, state: str) -> None:
        self.status.set_state(state)
        if self.tray:
            self.tray.setToolTip(f"{APP_NAME} — {self.status.text()[2:]}")
            self._tray_status.setText(f"Status: {self.status.text()[2:]}")

    def _update_badges(self) -> None:
        self.sidebar.items["presets"].set_badge(len(self.ctx.presets))

    # ── bandeja ──────────────────────────────────────────────────────────────
    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        menu = QMenu(self)
        self._tray_status = QAction("Status: Desconectado", self, enabled=False)
        menu.addAction(self._tray_status)
        menu.addSeparator()
        menu.addAction("Abrir", self.show_from_tray)
        menu.addAction("Sair", self.quit)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip(APP_NAME)
        self.tray.activated.connect(
            lambda reason: reason == QSystemTrayIcon.Trigger and self.show_from_tray())
        self.tray.show()

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit(self) -> None:
        self._really_quit = True
        self.close()

    def closeEvent(self, event) -> None:
        if self.tray and self.ctx.settings.close_to_tray and not self._really_quit:
            event.ignore()
            self.hide()
            self.tray.showMessage(APP_NAME, "Continua em execução na bandeja do sistema.",
                                  QSystemTrayIcon.Information, 2500)
            return
        self.ctx.controller.shutdown()
        if self.tray:
            self.tray.hide()
        event.accept()
        QApplication.instance().quit()
