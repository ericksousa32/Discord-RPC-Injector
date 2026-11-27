"""Startup: window, pages, theme and engine integration."""

import os
import unittest

from tests.helpers import AppTestCase

import discord_rpc_injector
from rpc_ui.core import engine
from rpc_ui.theme.palette import kde_tokens
from rpc_ui.theme.stylesheet import build_stylesheet


class StartupTests(AppTestCase):
    def test_window_opens_on_presence_page(self):
        self.assertTrue(self.win.isVisible())
        self.assertEqual(self.win.windowTitle(), "Discord RPC Injector")
        self.assertEqual(list(self.win.pages), ["presence", "presets", "log", "settings"])
        self.assertIs(self.win.current_page(), self.presence)
        self.assertEqual(self.win.sidebar.current(), "presence")
        self.assertEqual(self.win.header.title_label.text(), "Presence")
        self.assertEqual(self.win.header.subtitle_label.text(), "Not connected to Discord")

    def test_initial_state_is_disconnected(self):
        self.assertEqual(self.ctx.controller.state, "disconnected")
        self.assertEqual(self.win.status.state, "disconnected")
        self.assertFalse(self.presence.btn_apply.isEnabled())
        self.assertFalse(self.presence.btn_clear.isEnabled())
        self.assertTrue(self.presence.btn_connect.isEnabled())
        self.assertEqual(self.presence.btn_connect.text(), "Connect")

    def test_header_shows_page_actions(self):
        actions = self.win.header.action_widgets()
        self.assertEqual([a.text() for a in actions], ["Save preset", "Clear", "Apply"])
        self.assertFalse(self.win.header.search.isVisible())

    def test_system_theme_follows_kde_colors(self):
        tokens = self.ctx.theme.tokens
        self.assertEqual(self.ctx.theme.source, "kde")
        self.assertTrue(tokens.is_dark)
        self.assertEqual(tokens.window, "#202326")
        self.assertEqual(tokens.accent, "#97b3c2")
        self.assertIn("#97b3c2", self.app.styleSheet())

    def test_forced_light_and_dark_themes(self):
        self.ctx.theme.set_mode("light")
        self.assertFalse(self.ctx.theme.tokens.is_dark)
        light_qss = self.app.styleSheet()
        self.ctx.theme.set_mode("dark")
        self.assertTrue(self.ctx.theme.tokens.is_dark)
        self.assertNotEqual(light_qss, self.app.styleSheet())
        self.assertEqual(self.app.palette().window().color().name(), self.ctx.theme.tokens.window)

    def test_kde_tokens_missing_file(self):
        self.assertIsNone(kde_tokens(os.path.join(self.tmp.name, "nao-existe")))

    def test_stylesheet_builds_for_every_theme(self):
        from rpc_ui.theme.palette import DARK, LIGHT
        for t in (LIGHT, DARK, kde_tokens(self.kdeglobals)):
            qss = build_stylesheet(t)
            self.assertIn("#Sidebar", qss)
            self.assertEqual(qss.count("{"), qss.count("}"))

    def test_uses_engine(self):
        self.assertIs(engine.DiscordIPC, discord_rpc_injector.DiscordIPC)
        self.assertIs(engine.load_presets, discord_rpc_injector.load_presets)
        self.assertIs(engine.save_presets, discord_rpc_injector.save_presets)


if __name__ == "__main__":
    unittest.main()
