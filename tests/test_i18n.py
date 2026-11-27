"""Catálogos de texto: mesmas chaves e placeholders em todos os idiomas."""

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rpc_ui.i18n import CATALOGS, current_language, set_language, tr  # noqa: E402
from rpc_ui.i18n.en import MESSAGES as EN  # noqa: E402
from rpc_ui.i18n.pt_BR import MESSAGES as PT_BR  # noqa: E402
from tests.helpers import AppTestCase  # noqa: E402

PLACEHOLDER = re.compile(r"\{(\w+)\}")


class CatalogTests(unittest.TestCase):
    def tearDown(self):
        set_language("en")

    def test_default_language_is_english(self):
        self.assertEqual(current_language(), "en")
        self.assertEqual(tr("presence.btn_apply"), "Apply")

    def test_every_catalog_has_the_same_keys(self):
        for code, messages in CATALOGS.items():
            with self.subTest(language=code):
                self.assertEqual(set(messages), set(EN))

    def test_placeholders_match_in_every_language(self):
        for key in EN:
            expected = set(PLACEHOLDER.findall(EN[key]))
            self.assertEqual(set(PLACEHOLDER.findall(PT_BR[key])), expected, key)

    def test_switching_language_changes_the_text(self):
        set_language("pt_BR")
        self.assertEqual(tr("presence.btn_apply"), "Aplicar")
        self.assertEqual(tr("ctrl.connected_via", path="x"), "Conectado via x")
        set_language("en")
        self.assertEqual(tr("ctrl.connected_via", path="x"), "Connected via x")

    def test_unknown_language_is_rejected(self):
        with self.assertRaises(ValueError):
            set_language("fr")
        self.assertEqual(current_language(), "en")


class LiveLanguageTests(AppTestCase):
    def tearDown(self):
        set_language("en")
        super().tearDown()

    def test_picking_a_language_retranslates_the_window(self):
        self.assertEqual(self.presence.btn_apply.text(), "Apply")
        picker = self.win.settings_page.language
        picker.setCurrentIndex(picker.findData("pt_BR"))
        self.process()
        self.assertEqual(self.presence.btn_apply.text(), "Aplicar")
        self.assertEqual(self.win.sidebar.items["presets"].text(), "Predefinições")
        self.assertEqual(self.win.header.title_label.text(), "Presença")
        self.assertEqual(self.ctx.settings.language, "pt_BR")
        self.assertEqual(current_language(), "pt_BR")


if __name__ == "__main__":
    unittest.main()
