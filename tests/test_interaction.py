"""Interação: conexão, aplicar/limpar, validação, predefinições, busca, registro e diálogos."""

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog

from rpc_ui.core.models import Presence
from rpc_ui.widgets import ConfirmDialog, TextInputDialog
from tests.helpers import AppTestCase, FakeIPC

PRESETS = {
    "Fedora": {"app_id": "111", "details": "Just Chilling", "state": "(KDE Plasma)", "show_elapsed": True},
    "Virt-Manager": {"app_id": "222", "details": "Running Windows 10", "state": "via Linux",
                     "btn1_label": "Site", "btn1_url": "https://example.org", "show_elapsed": False},
}


class ConnectionTests(AppTestCase):
    def test_invalid_app_id_shows_error_and_stays_disconnected(self):
        self.connect("abc")
        self.assertEqual(self.ctx.controller.state, "disconnected")
        self.assertEqual(FakeIPC.instances, [])
        self.assertIn(("Application ID inválido", "err"), self.toasts())

    def test_connect_enables_actions_and_updates_status(self):
        self.connect()
        self.assertEqual(self.ctx.controller.state, "connected")
        self.assertEqual(self.win.status.state, "connected")
        self.assertEqual(self.presence.status_pill.state, "connected")
        self.assertTrue(self.presence.btn_apply.isEnabled())
        self.assertEqual(self.presence.btn_connect.text(), "Desconectar")
        self.assertFalse(self.presence.fields["app_id"].isEnabled())
        self.assertIn("discord-ipc-0", self.presence.socket_label.text())
        self.assertEqual(self.ctx.settings.last_app_id, "123456789012345678")

    def test_connection_failure_is_reported(self):
        FakeIPC.fail_connect = "Socket do Discord não encontrado."
        self.connect()
        self.assertEqual(self.ctx.controller.state, "disconnected")
        self.assertIn(("Erro de conexão", "err"), self.toasts())
        self.assertEqual(self.ctx.controller.history[-1].level, "err")

    def test_disconnect(self):
        self.connect()
        self.presence.btn_connect.click()
        self.assertEqual(self.ctx.controller.state, "disconnected")
        self.assertTrue(FakeIPC.instances[0].closed)
        self.assertFalse(self.presence.btn_apply.isEnabled())


class PresenceTests(AppTestCase):
    def fill(self, **values):
        for k, v in values.items():
            self.presence.fields[k].setText(v)

    def test_apply_sends_activity(self):
        self.connect()
        self.fill(details="Codando", state="Python", btn1_label="Repo", btn1_url="https://example.org",
                  party_size="1", party_max="4")
        self.presence.btn_apply.click()
        self.process()
        sent = FakeIPC.instances[0].sent[-1]
        self.assertEqual(sent["details"], "Codando")
        self.assertEqual(sent["buttons"], [{"label": "Repo", "url": "https://example.org"}])
        self.assertEqual(sent["party"]["size"], [1, 4])
        self.assertIn("timestamps", sent)
        self.assertIn(("Presença atualizada", "ok"), self.toasts())
        self.assertEqual(self.win.header.subtitle_label.text(), "Presença ativa no Discord")

        self.fill(details="Outra coisa")
        self.assertEqual(self.win.header.subtitle_label.text(), "Alterações não aplicadas")

    def test_validation_blocks_send(self):
        self.connect()
        self.fill(btn1_label="Repo", btn1_url="example.org")
        self.presence.btn_apply.click()
        self.assertEqual(FakeIPC.instances[0].sent, [])
        self.assertEqual(self.presence.fields["btn1_url"].property("invalid"), "true")
        self.assertIn(("Verifique os campos", "err"), self.toasts())

    def test_clear_presence(self):
        self.connect()
        self.presence.btn_apply.click()
        self.presence.btn_clear.click()
        self.assertEqual(FakeIPC.instances[0].cleared, 1)
        self.assertIsNone(self.ctx.controller.start_ts)
        self.assertIn(("Presença removida", "warn"), self.toasts())

    def test_send_failure_disconnects(self):
        self.connect()
        FakeIPC.fail_send = "Conexão encerrada pelo Discord."
        self.presence.btn_apply.click()
        self.assertEqual(self.ctx.controller.state, "disconnected")
        self.assertIn(("Falha ao aplicar", "err"), self.toasts())

    def test_preview_follows_fields(self):
        self.fill(details="Jogando xadrez", state="Ranqueada", party_size="2", party_max="2")
        self.assertEqual(self.presence.preview.details.text(), "Jogando xadrez")
        self.assertEqual(self.presence.preview.state.text(), "Ranqueada (2 de 2)")
        self.assertTrue(self.presence.preview.btn1.isHidden())


class PayloadFormatTests(unittest.TestCase):
    """Formato do payload enviado ao Discord e das chaves salvas nas predefinições."""

    # Activity esperada: campos vazios omitidos, espaços removidos, botão incompleto ignorado.
    EXPECTED_ACTIVITY = {
        "details": "D", "state": "S", "timestamps": {"start": 1234},
        "assets": {"large_image": "big", "small_text": "tip"},
        "buttons": [{"label": "A", "url": "https://a"}],
        "party": {"id": "pid", "size": [2, 5]},
    }
    # Chaves gravadas em presets.json (alterar quebra predefinições já salvas).
    PRESET_KEYS = [
        "app_id", "details", "state", "large_key", "large_text", "small_key", "small_text",
        "btn1_label", "btn1_url", "btn2_label", "btn2_url", "party_size", "party_max",
        "party_id", "show_elapsed",
    ]

    def test_activity_payload(self):
        data = {"details": " D ", "state": "S", "large_key": "big", "small_text": "tip",
                "btn1_label": "A", "btn1_url": "https://a", "btn2_label": "B", "btn2_url": "",
                "party_size": "2", "party_max": "5", "party_id": "pid", "show_elapsed": True}
        self.assertEqual(Presence.from_dict(data).build_activity(1234), self.EXPECTED_ACTIVITY)

    def test_round_trip_with_preset_format(self):
        p = Presence.from_dict(PRESETS["Virt-Manager"])
        self.assertEqual(Presence.from_dict(p.to_dict()), p)
        self.assertEqual(list(p.to_dict()), self.PRESET_KEYS)


class PresetTests(AppTestCase):
    initial_presets = PRESETS

    def setUp(self):
        super().setUp()
        self.page = self.win.presets_page
        self.win.navigate("presets")

    def test_list_and_badge(self):
        self.assertEqual(self.page.visible_names(), ["Fedora", "Virt-Manager"])
        self.assertEqual(self.win.sidebar.items["presets"].badge.text(), "2")
        self.assertEqual(self.win.header.subtitle_label.text(), "2 salvas")

    def test_search_filters_and_shows_empty_state(self):
        self.win.header.search.setText("windows")
        self.assertEqual(self.page.visible_names(), ["Virt-Manager"])
        self.win.header.search.setText("nada disso")
        self.assertIs(self.page.stack.currentWidget(), self.page.no_results)
        self.win.header.search.clear()
        self.assertIs(self.page.stack.currentWidget(), self.page.list)

    def test_load_fills_editor_and_navigates(self):
        self.page.select("Virt-Manager")
        self.page.btn_load.click()
        self.assertEqual(self.win.sidebar.current(), "presence")
        self.assertEqual(self.presence.fields["details"].text(), "Running Windows 10")
        self.assertEqual(self.presence.fields["btn1_url"].text(), "https://example.org")
        self.assertFalse(self.presence.show_elapsed.isChecked())

    def test_save_current_as_preset(self):
        self.win.navigate("presence")
        self.presence.fields["details"].setText("Novo")
        self.dialogs.texts = ["Minha presença"]
        self.presence.btn_save.click()
        self.assertIn("Minha presença", self.ctx.presets)
        self.assertEqual(self.saved[-1]["Minha presença"]["details"], "Novo")
        self.assertEqual(self.win.sidebar.items["presets"].badge.text(), "3")
        self.assertIn(("Predefinição salva", "ok"), self.toasts())

    def test_save_cancelled(self):
        self.dialogs.texts = [None]
        self.page.btn_new.click()
        self.assertEqual(len(self.ctx.presets), 2)
        self.assertEqual(self.saved, [])

    def test_rename_rejects_duplicates_and_renames(self):
        self.page.select("Fedora")
        self.dialogs.texts = ["Virt-Manager"]
        self.page.btn_rename.click()
        self.assertIn("Fedora", self.ctx.presets)
        self.dialogs.texts = ["Plasma"]
        self.page.btn_rename.click()
        self.assertEqual(self.page.visible_names(), ["Plasma", "Virt-Manager"])
        self.assertEqual(self.page.selected_name(), "Plasma")

    def test_delete_requires_confirmation_and_can_be_undone(self):
        self.page.select("Fedora")
        self.dialogs.confirms = [False]
        self.page.btn_delete.click()
        self.assertIn("Fedora", self.ctx.presets)

        self.dialogs.confirms = [True]
        self.page.btn_delete.click()
        self.assertNotIn("Fedora", self.ctx.presets)
        self.assertEqual(self.dialogs.asked[-1], ("confirm", "Excluir predefinição?", True))
        toast = self.ctx.toasts.toasts[-1]
        self.assertEqual(toast.action_button.text(), "Desfazer")
        toast.action_button.click()
        self.assertIn("Fedora", self.ctx.presets)

    def test_empty_state_when_no_presets(self):
        for name in list(self.ctx.presets.names()):
            self.ctx.presets.delete(name)
        self.assertIs(self.page.stack.currentWidget(), self.page.empty)
        self.assertFalse(self.page.btn_load.isEnabled())
        self.assertEqual(self.win.header.subtitle_label.text(), "Nenhuma salva")


class PresetPickerTests(AppTestCase):
    """Lista de predefinições aberta ao clicar no campo App ID do card Conexão."""

    initial_presets = PRESETS

    def setUp(self):
        super().setUp()
        self.field = self.presence.fields["app_id"]
        self.picker = self.presence.preset_suggestions

    def click_field(self):
        QTest.mouseClick(self.field, Qt.LeftButton)
        self.process()

    def test_click_opens_list_with_all_presets(self):
        self.click_field()
        self.assertTrue(self.picker.is_open())
        self.assertEqual(self.picker.visible_keys(), ["Fedora", "Virt-Manager"])

    def test_typing_filters_by_app_id(self):
        self.field.clear()
        QTest.keyClicks(self.field, "22")
        self.process()
        self.assertTrue(self.picker.is_open())
        self.assertEqual(self.picker.visible_keys(), ["Virt-Manager"])
        QTest.keyClicks(self.field, "9")
        self.assertFalse(self.picker.is_open())   # nada corresponde

    def test_choosing_loads_preset(self):
        self.click_field()
        self.picker.choose_row(1)
        self.process()
        self.assertFalse(self.picker.is_open())
        self.assertEqual(self.field.text(), "222")
        self.assertEqual(self.presence.fields["details"].text(), "Running Windows 10")
        self.assertEqual(self.presence.fields["btn1_label"].text(), "Site")
        self.assertIn(('"Virt-Manager" carregada', "info"), self.toasts())
        self.assertEqual(self.ctx.controller.history[-1].message, '"Virt-Manager" carregada.')

    def test_keyboard_pick_does_not_connect(self):
        self.field.setFocus()
        QTest.keyClick(self.field, Qt.Key_Down)        # abre a lista
        self.assertTrue(self.picker.is_open())
        popup = self.picker.completer.popup()
        QTest.keyClick(popup, Qt.Key_Down)
        QTest.keyClick(popup, Qt.Key_Return)
        self.process()
        self.assertEqual(self.presence.fields["details"].text(), "Just Chilling")
        self.assertEqual(FakeIPC.instances, [])        # Enter não disparou "Conectar"
        self.assertEqual(self.ctx.controller.state, "disconnected")

    def test_enter_without_selection_still_connects(self):
        self.field.clear()
        QTest.keyClicks(self.field, "111")
        self.assertTrue(self.picker.is_open())         # lista aberta, nada escolhido
        QTest.keyClick(self.picker.completer.popup(), Qt.Key_Return)
        self.process()
        self.assertEqual(self.ctx.controller.state, "connected")
        self.assertEqual(FakeIPC.instances[0].client_id, "111")

    def test_escape_closes_without_loading(self):
        self.click_field()
        QTest.keyClick(self.picker.completer.popup(), Qt.Key_Escape)
        self.process()
        self.assertFalse(self.picker.is_open())
        self.assertEqual(self.presence.fields["details"].text(), "")

    def test_not_available_while_connected(self):
        self.connect()
        self.assertFalse(self.picker.open())
        self.assertFalse(self.picker.is_open())

    def test_list_follows_store_changes(self):
        self.ctx.presets.put("Novo", Presence(app_id="333", details="Teste"))
        self.ctx.presets.delete("Fedora")
        self.click_field()
        self.assertEqual(self.picker.visible_keys(), ["Novo", "Virt-Manager"])


class PresetPickerEmptyTests(AppTestCase):
    def test_no_list_without_presets(self):
        QTest.mouseClick(self.presence.fields["app_id"], Qt.LeftButton)
        self.process()
        self.assertFalse(self.presence.preset_suggestions.is_open())


class LogTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.page = self.win.log_page
        self.win.navigate("log")

    def test_empty_then_entries(self):
        self.assertIs(self.page.stack.currentWidget(), self.page.empty)
        self.connect("abc")
        self.connect()
        self.assertIs(self.page.stack.currentWidget(), self.page.list)
        self.assertEqual(self.page.list.count(), 2)

    def test_filter_by_text_and_level_and_clear(self):
        self.ctx.controller.log("alpha", "ok")
        self.ctx.controller.log("beta", "err")
        self.win.header.search.setText("alp")
        self.assertEqual(self.page.list.count(), 1)
        self.win.header.search.clear()
        self.page.level.setCurrentIndex(self.page.level.findData("err"))
        self.assertEqual(self.page.list.count(), 1)
        self.page.level.setCurrentIndex(0)
        self.page.btn_clear.click()
        self.assertIs(self.page.stack.currentWidget(), self.page.empty)


class SettingsTests(AppTestCase):
    def test_theme_choice_is_applied_and_persisted(self):
        page = self.win.settings_page
        page.theme_buttons["light"].click()
        self.assertEqual(self.ctx.settings.theme, "light")
        self.assertEqual(self.ctx.theme.mode, "light")
        self.assertFalse(self.ctx.theme.tokens.is_dark)
        page.theme_buttons["system"].click()
        self.assertEqual(self.ctx.theme.source, "kde")

    def test_close_to_tray_toggle(self):
        self.win.settings_page.close_to_tray.setChecked(False)
        self.assertFalse(self.ctx.settings.close_to_tray)


class DialogWidgetTests(AppTestCase):
    def test_text_input_dialog_validation(self):
        dlg = TextInputDialog("Salvar", "Nome:", "", validate=lambda t: "duplicado" if t == "x" else None)
        self.assertFalse(dlg.ok_button.isEnabled())          # vazio
        dlg.field.setText("x")
        self.assertFalse(dlg.ok_button.isEnabled())
        self.assertEqual(dlg.error_label.text(), "duplicado")
        dlg.field.setText("  ok  ")
        self.assertTrue(dlg.ok_button.isEnabled())
        dlg.ok_button.click()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        self.assertEqual(dlg.value(), "ok")

    def test_confirm_dialog_destructive(self):
        dlg = ConfirmDialog("Excluir?", "Tem certeza?", "Excluir", destructive=True)
        self.assertEqual(dlg.ok_button.property("variant"), "danger")
        dlg.cancel_button.click()
        self.assertEqual(dlg.result(), QDialog.Rejected)

    def test_toasts_are_capped(self):
        for i in range(6):
            self.ctx.notify(f"n{i}")
        self.assertEqual(len(self.ctx.toasts.toasts), 3)
        self.assertEqual(self.toasts()[-1], ("n5", "info"))


if __name__ == "__main__":
    unittest.main()
