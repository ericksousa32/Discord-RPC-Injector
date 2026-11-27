"""Shared test infrastructure: Qt offscreen, fake IPC and scripted dialogs."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PySide6.QtCore import QEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from rpc_ui.app import build_window, create_app  # noqa: E402
from rpc_ui.context import AppContext  # noqa: E402
from rpc_ui.core.controller import PresenceController  # noqa: E402
from rpc_ui.core.presets import PresetStore  # noqa: E402
from rpc_ui.core.settings import AppSettings  # noqa: E402

DARK_KDEGLOBALS = """[General]
AccentColor=151,179,194

[Colors:Window]
BackgroundNormal=32,35,38
ForegroundNormal=252,252,252

[Colors:View]
BackgroundNormal=20,22,24

[Colors:Selection]
BackgroundNormal=111,131,143
ForegroundNormal=255,255,255
"""


class FakeIPC:
    """Replaces ``DiscordIPC``, recording the calls."""

    instances: list["FakeIPC"] = []
    fail_connect: str | None = None
    fail_send: str | None = None

    def __init__(self, client_id):
        self.client_id = client_id
        self.sent = []
        self.cleared = 0
        self.closed = False
        FakeIPC.instances.append(self)

    def connect(self):
        if FakeIPC.fail_connect:
            raise ConnectionError(FakeIPC.fail_connect)
        return "/run/user/1000/app/com.discordapp.Discord/discord-ipc-0"

    def set_activity(self, activity):
        if FakeIPC.fail_send:
            raise ConnectionError(FakeIPC.fail_send)
        self.sent.append(activity)
        return {"evt": None}

    def clear_activity(self):
        self.cleared += 1
        return {"evt": None}

    def disconnect(self):
        self.closed = True

    @classmethod
    def reset(cls):
        cls.instances, cls.fail_connect, cls.fail_send = [], None, None


class ScriptedDialogs:
    """Answers dialogs with predefined values and records the questions."""

    def __init__(self):
        self.texts: list = []
        self.confirms: list = []
        self.asked: list = []

    def ask_text(self, title, label, value="", confirm_text="Save", validate=None):
        self.asked.append(("text", title, value))
        answer = self.texts.pop(0) if self.texts else None
        if answer is not None and validate and validate(answer):
            return None  # the real dialog would not allow confirming
        return answer

    def confirm(self, title, text, confirm_text="Confirmar", destructive=False):
        self.asked.append(("confirm", title, destructive))
        return self.confirms.pop(0) if self.confirms else False


def sync_runner(fn):
    fn()


class AppTestCase(unittest.TestCase):
    """Creates an isolated window per test (in-memory presets, temporary settings)."""

    initial_presets: dict = {}

    @classmethod
    def setUpClass(cls):
        cls.app = create_app([])

    def setUp(self):
        FakeIPC.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.saved: list[dict] = []
        data = {k: dict(v) for k, v in self.initial_presets.items()}
        kde = os.path.join(self.tmp.name, "kdeglobals")
        with open(kde, "w") as f:
            f.write(DARK_KDEGLOBALS)
        self.kdeglobals = kde
        self.dialogs = ScriptedDialogs()
        self.ctx = AppContext(
            controller=PresenceController(ipc_factory=FakeIPC, runner=sync_runner),
            presets=PresetStore(lambda: data, lambda d: self.saved.append(dict(d))),
            settings=AppSettings(os.path.join(self.tmp.name, "settings.ini")),
            dialogs=self.dialogs,
        )
        self.win = build_window(self.app, self.ctx, enable_tray=False, kdeglobals=kde)
        self.win.show()
        self.process()

    def tearDown(self):
        for t in list(self.ctx.toasts.toasts):
            t.dismiss()
        self.win._really_quit = True
        self.win.hide()
        self.win.deleteLater()
        self.ctx.theme.deleteLater()   # disconnects the theme from the QApplication
        self.process()
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.tmp.cleanup()

    def process(self):
        QApplication.processEvents()

    # shortcuts
    @property
    def presence(self):
        return self.win.presence_page

    def toasts(self):
        return [(t.title_label.text(), t.tone) for t in self.ctx.toasts.toasts]

    def connect(self, app_id="123456789012345678"):
        self.presence.fields["app_id"].setText(app_id)
        self.presence.btn_connect.click()
        self.process()
