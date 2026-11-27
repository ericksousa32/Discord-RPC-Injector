"""Text catalogs: same keys and placeholders in every language, live switching and persistence."""

import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtCore import QEvent, QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from rpc_ui.app import build_window  # noqa: E402
from rpc_ui.context import AppContext  # noqa: E402
from rpc_ui.core.controller import PresenceController  # noqa: E402
from rpc_ui.core.presets import PresetStore  # noqa: E402
from rpc_ui.core.models import Presence  # noqa: E402
from rpc_ui.core.settings import AppSettings  # noqa: E402
from rpc_ui.i18n import CATALOGS, current_language, set_language, tr  # noqa: E402
from rpc_ui.i18n.en import MESSAGES as EN  # noqa: E402
from rpc_ui.i18n.pt_BR import MESSAGES as PT_BR  # noqa: E402
from rpc_ui.pages.log import LEVEL_FILTERS  # noqa: E402
from rpc_ui.pages.presence import LABEL_KEYS, PLACEHOLDER_KEYS  # noqa: E402
from rpc_ui.widgets.suggestions import KEY_ROLE, SUBTITLE_ROLE  # noqa: E402
from tests.helpers import AppTestCase, FakeIPC, sync_runner  # noqa: E402

PLACEHOLDER = re.compile(r"\{(\w+)\}")
SOURCE_DIR = os.path.join(ROOT, "rpc_ui")
DOTTED_LITERAL = re.compile(r'"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)"')
FILE_SUFFIXES = ("py", "png", "svg", "json", "ini", "desktop")  # look like keys, are file names


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

    def test_no_message_is_empty(self):
        for code, messages in CATALOGS.items():
            for key, text in messages.items():
                with self.subTest(language=code, key=key):
                    self.assertTrue(text.strip(), "empty message")

    def test_every_key_used_in_code_exists_in_the_catalog(self):
        # tr() falls back to English and then to the raw key, so a missing key would
        # show up silently. Scan the source for dotted keys and check each one.
        used = {}
        for dirpath, _dirs, files in os.walk(SOURCE_DIR):
            if os.path.basename(dirpath) == "i18n":
                continue
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as f:
                    for key in DOTTED_LITERAL.findall(f.read()):
                        if key.rsplit(".", 1)[-1] not in FILE_SUFFIXES:
                            used.setdefault(key, os.path.relpath(path, ROOT))
        missing = {key: where for key, where in used.items() if key not in EN}
        self.assertEqual(missing, {})

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

    def _pick(self, code: str) -> None:
        picker = self.win.settings_page.language
        picker.setCurrentIndex(picker.findData(code))
        self.process()

    def test_picking_a_language_retranslates_the_window(self):
        self.assertEqual(self.presence.btn_apply.text(), "Apply")
        self._pick("pt_BR")
        self.assertEqual(self.presence.btn_apply.text(), "Aplicar")
        self.assertEqual(self.win.sidebar.items["presets"].text(), "Predefinições")
        self.assertEqual(self.win.header.title_label.text(), "Presença")
        self.assertEqual(self.ctx.settings.language, "pt_BR")
        self.assertEqual(current_language(), "pt_BR")

    def test_sidebar_and_top_bar_follow_the_language_on_every_page(self):
        self._pick("pt_BR")
        self.assertEqual([label.text() for label, _ in self.win._section_labels],
                         [tr("nav.section.general").upper(), tr("nav.section.app").upper()])
        for key, page in self.win.pages.items():
            with self.subTest(page=key):
                self.win.navigate(key)
                self.process()
                self.assertEqual(self.win.sidebar.items[key].text(), tr(page.title_key))
                self.assertEqual(self.win.header.title_label.text(), tr(page.title_key))
                self.assertEqual(self.win.header.subtitle_label.text(), page.subtitle())

    def test_top_bar_actions_follow_the_language(self):
        self.win.navigate("presets")
        self._pick("pt_BR")
        texts = [w.text() for w in self.win.header.action_widgets()]
        self.assertEqual(texts, [tr("presets.btn_new"), tr("presets.btn_rename"),
                                 tr("presets.btn_delete"), tr("presets.btn_load")])
        self.assertEqual(texts[-1], "Carregar")

    def test_open_page_contents_follow_the_language(self):
        self._pick("pt_BR")
        page = self.presence
        for form in page._forms:
            for key, label in form.labels.items():
                if key in LABEL_KEYS:
                    self.assertEqual(label.text(), tr(LABEL_KEYS[key]), key)
        for key, placeholder_key in PLACEHOLDER_KEYS.items():
            self.assertEqual(page.fields[key].placeholderText(), tr(placeholder_key), key)
        self.assertEqual(self.win.settings_page.close_to_tray.text(), tr("settings.close_to_tray"))
        self.assertEqual(self.win.presets_page.btn_new.text(), tr("presets.btn_new"))
        log = self.win.log_page
        self.assertEqual([log.level.itemText(i) for i in range(log.level.count())],
                         [tr(key) for key, _ in LEVEL_FILTERS])

    def test_app_id_suggestion_subtitles_follow_the_language(self):
        # A preset without text shows "No text" under its name in the App ID list.
        # PresencePage builds those rows itself, so a switch must rebuild them too.
        self.ctx.presets.put("Blank", Presence(app_id="42"))
        self.assertEqual(self._suggestion_subtitle("Blank"), "No text")
        self._pick("pt_BR")
        self.assertEqual(self._suggestion_subtitle("Blank"), "Sem texto")

    def _suggestion_subtitle(self, key: str) -> str:
        model = self.presence.preset_suggestions._model
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.data(KEY_ROLE) == key:
                return item.data(SUBTITLE_ROLE)
        self.fail(f"no App ID suggestion named {key!r}")

    def test_switching_back_to_english_restores_the_text(self):
        self._pick("pt_BR")
        self._pick("en")
        self.assertEqual(self.presence.btn_apply.text(), "Apply")
        self.assertEqual(self.win.sidebar.items["presets"].text(), "Presets")
        self.assertEqual(self.win.header.title_label.text(), "Presence")

    def test_language_names_stay_in_their_own_language(self):
        picker = self.win.settings_page.language
        names_en = [picker.itemText(i) for i in range(picker.count())]
        self._pick("pt_BR")
        names_pt = [picker.itemText(i) for i in range(picker.count())]
        self.assertEqual(names_en, names_pt)
        self.assertEqual(names_pt, ["English", "Português (Brasil)"])

    def test_tray_menu_and_tooltip_follow_the_language(self):
        self.win._setup_tray()  # the tests run without a tray; create it for this check
        self._pick("pt_BR")
        self.assertEqual(self.win._tray_open.text(), "Abrir")
        self.assertEqual(self.win._tray_quit.text(), "Sair")
        self.assertEqual(self.win._tray_status.text(), "Status: Desconectado")
        self.assertEqual(self.win.tray.toolTip(), "Discord RPC Injector — Desconectado")
        self._pick("en")
        self.assertEqual(self.win._tray_open.text(), "Open")
        self.assertEqual(self.win._tray_quit.text(), "Quit")
        self.assertEqual(self.win._tray_status.text(), "Status: Disconnected")
        self.assertEqual(self.win.tray.toolTip(), "Discord RPC Injector — Disconnected")
        self.win.tray.hide()

    def test_toasts_use_the_language_active_when_they_are_shown(self):
        self._pick("pt_BR")
        self.presence.fields["btn1_label"].setText("Site")  # label without URL: invalid
        self.presence.apply_presence()
        self.assertIn((tr("notify.check_fields"), "err"), self.toasts())
        self.presence.fields["app_id"].setText("abc")
        self.presence.btn_connect.click()
        self.assertIn((tr("ctrl.invalid_app_id.title"), "err"), self.toasts())
        self.assertIn(("Verifique os campos", "err"), self.toasts())
        self.assertIn(("Application ID inválido", "err"), self.toasts())

    def test_chosen_language_is_restored_on_the_next_startup(self):
        self._pick("pt_BR")
        settings_path = os.path.join(self.tmp.name, "settings.ini")
        self.assertEqual(AppSettings(settings_path).language, "pt_BR")
        set_language("en")  # as in a new process, before the window is built

        ctx = AppContext(PresenceController(ipc_factory=FakeIPC, runner=sync_runner),
                         PresetStore(lambda: {}, lambda d: None),
                         AppSettings(settings_path))
        win = build_window(self.app, ctx, enable_tray=False, kdeglobals=self.kdeglobals)
        self.addCleanup(self._discard_window, win, ctx)

        self.assertEqual(current_language(), "pt_BR")
        self.assertEqual(win.settings_page.language.currentData(), "pt_BR")
        self.assertEqual(win.presence_page.btn_apply.text(), "Aplicar")
        self.assertEqual(win.sidebar.items["presets"].text(), "Predefinições")

    def test_unknown_saved_language_falls_back_to_english(self):
        settings_path = os.path.join(self.tmp.name, "settings.ini")
        qs = QSettings(settings_path, QSettings.IniFormat)
        qs.setValue("language", "fr")
        qs.sync()
        self.assertEqual(AppSettings(settings_path).language, "en")

    def _discard_window(self, win, ctx):
        win._really_quit = True
        win.hide()
        win.deleteLater()
        ctx.theme.deleteLater()  # disconnects the theme from the QApplication
        self.process()
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
