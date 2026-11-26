"""Navegação: barra lateral, barra superior, busca por página e atalhos."""

import unittest

from PySide6.QtGui import QKeySequence

from tests.helpers import AppTestCase

EXPECTED = {
    "presence": ("Presença", False),
    "presets": ("Predefinições", True),
    "log": ("Registro", True),
    "settings": ("Configurações", False),
}


class NavigationTests(AppTestCase):
    def test_sidebar_click_switches_page_and_header(self):
        for key, (title, searchable) in EXPECTED.items():
            with self.subTest(page=key):
                self.win.sidebar.items[key].click()
                self.process()
                self.assertIs(self.win.current_page(), self.win.pages[key])
                self.assertEqual(self.win.sidebar.current(), key)
                self.assertEqual(self.win.header.title_label.text(), title)
                self.assertEqual(self.win.header.search.isVisible(), searchable)

    def test_header_actions_follow_page(self):
        self.win.navigate("presets")
        texts = [w.text() for w in self.win.header.action_widgets()]
        self.assertEqual(texts, ["Nova a partir da atual", "Renomear", "Excluir", "Carregar"])
        self.win.navigate("settings")
        self.assertEqual(self.win.header.action_widgets(), [])
        self.win.navigate("presence")
        self.assertIn("Aplicar", [w.text() for w in self.win.header.action_widgets()])
        # os botões da página anterior não ficam órfãos/visíveis no cabeçalho
        self.assertFalse(self.win.presets_page.btn_load.isVisible())

    def test_search_text_is_kept_per_page(self):
        self.win.navigate("presets")
        self.win.header.search.setText("fedora")
        self.win.navigate("log")
        self.assertEqual(self.win.header.search.text(), "")
        self.win.navigate("presets")
        self.assertEqual(self.win.header.search.text(), "fedora")

    def test_find_shortcut_goes_to_searchable_page(self):
        self.win.navigate("presence")
        self.win.focus_search()
        self.process()
        self.assertEqual(self.win.sidebar.current(), "presets")
        self.win.navigate("log")
        self.win.focus_search()
        self.assertEqual(self.win.sidebar.current(), "log")

    def test_navigation_shortcuts_are_assigned(self):
        shortcuts = {k: item.shortcut().toString() for k, item in self.win.sidebar.items.items()}
        self.assertEqual(shortcuts["presence"], QKeySequence("Ctrl+1").toString())
        self.assertEqual(shortcuts["presets"], QKeySequence("Ctrl+2").toString())
        self.assertEqual(shortcuts["log"], QKeySequence("Ctrl+3").toString())

    def test_subtitle_updates_live(self):
        self.win.navigate("log")
        self.assertEqual(self.win.header.subtitle_label.text(), "Sem eventos")
        self.ctx.controller.log("algo deu errado", "err")
        self.assertEqual(self.win.header.subtitle_label.text(), "1 evento · 1 erro")


if __name__ == "__main__":
    unittest.main()
