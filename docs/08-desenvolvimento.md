# 8. Development

> **Summary:** `python3 -m unittest discover -s tests -t .` runs all the tests without opening
> windows and without needing Discord. New screens are a `Page` class; new components go into
> `widgets/`; colours always come from the theme tokens.

## Running the tests

In the project folder:

```bash
python3 -m unittest discover -s tests -t .
```

To see the name of each test, add `-v`. To run a single file:

```bash
python3 -m unittest tests.test_engine -v
```

The tests:

- use Qt in **offscreen** mode (no window appears);
- **do not** connect to the real Discord: they use a fake IPC or a server that imitates Discord;
- **do not** touch your files: presets stay in memory or in temporary folders.

### What each file covers

| File                   | Covers                                                                 |
|------------------------|------------------------------------------------------------------------|
| `test_startup.py`      | Window opens, home page, disconnected state, KDE/light/dark theme       |
| `test_navigation.py`   | Sidebar, top bar, per-page search, shortcuts                           |
| `test_interaction.py`  | Connect, apply, clear, validation, presets (save, rename, delete/undo), preset list on the App ID field, log, dialogs, notifications, payload format |
| `test_engine.py`       | Socket of each type of installation, timeouts, refusal, abandoned socket, protocol, saving presets, `.desktop` shortcut |

### Test tools (`tests/helpers.py`)

| Tool              | Purpose                                                            |
|-------------------|--------------------------------------------------------------------|
| `AppTestCase`     | Creates an isolated window per test (in-memory presets, temporary settings, fake `kdeglobals`) |
| `FakeIPC`         | Replaces `DiscordIPC`; records what was sent; can simulate failures (`fail_connect`, `fail_send`) |
| `ScriptedDialogs` | Answers dialogs with preset values (`texts`, `confirms`)            |
| `sync_runner`     | Runs the controller's "background" immediately, keeping tests deterministic |

In `test_engine.py`, the `FakeDiscord` class opens a real Unix socket and behaves like Discord
in the `ready`, `delay`, `reject` and `silent` modes.

### Example of an interface test

```python
from tests.helpers import AppTestCase, FakeIPC

class MyTest(AppTestCase):
    def test_apply_sends_details(self):
        self.connect()                                   # connects with the FakeIPC
        self.presence.fields["details"].setText("Coding")
        self.presence.btn_apply.click()
        self.assertEqual(FakeIPC.instances[0].sent[-1]["details"], "Coding")
```

## How to add a page

1. Create `rpc_ui/pages/my_page.py`:

   ```python
   from .base import Page
   from ..widgets import Button, Card

   class MyPage(Page):
       key = "my"
       title = "My page"
       icon = "help-about"                 # freedesktop icon name
       search_placeholder = None           # or "Search…" to enable search

       def __init__(self, ctx, parent=None):
           super().__init__(parent)
           self.ctx = ctx
           self.btn = Button("Do something", "dialog-ok", "primary", on_click=self.do_it)
           # ... build the layout with Card, FormGrid etc.

       def subtitle(self):
           return "Short description"

       def header_actions(self):
           return [self.btn]

       def do_it(self):
           self.ctx.notify("Done!", tone="ok")
   ```

2. Export it in `rpc_ui/pages/__init__.py`.
3. Register it in `MainWindow.__init__` with `self._add_page(MyPage(ctx), "Ctrl+4")`.
4. Add a case to `tests/test_navigation.py`.

## How to add a widget

- Put it in `rpc_ui/widgets/` and export it in `widgets/__init__.py`.
- **No business logic**: the widget receives data and emits signals.
- **No fixed colours**: set an `objectName` (or the `variant` property with `set_prop`) and add
  the rules in `theme/stylesheet.py` using the tokens.

## Changing the theme

- New colours: add the field to `Tokens` (`theme/palette.py`), fill it in `LIGHT`, `DARK` and in
  `_from_colors` (System mode).
- Styles: edit `build_stylesheet()` in `theme/stylesheet.py`.
- Icons: `widgets/icons.py` uses the system icon theme (Breeze on KDE) and draws a simple symbol
  when the icon does not exist.

## Conventions

- Documentation is written in **English**. Interface strings are being moved to the translation
  layer; the language selector in Settings adds English and Brazilian Portuguese.
- Each file has one responsibility; pages do not import the engine directly (use the `AppContext`).
- Network operations always go through the `PresenceController` (never on the interface thread).
- Every new behaviour comes with a test.

## Generating screenshots without opening windows

```python
import os; os.environ["QT_QPA_PLATFORM"] = "offscreen"
from rpc_ui.app import create_app, build_window

app = create_app([])
win = build_window(app, enable_tray=False)
win.resize(1180, 760); win.show(); app.processEvents()
win.grab().save("screenshot.png")
```

---

Previous: [Architecture](07-arquitetura.md) · Next: [Engine reference](09-referencia-do-motor.md)
