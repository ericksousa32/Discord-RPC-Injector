<p align="center">
  <img src="rpc_icon.svg" width="96" alt="Discord RPC Injector icon">
</p>

<h1 align="center">Discord RPC Injector</h1>

<p align="center">
  Set your Discord <b>Rich Presence</b> ("Playing…") on Linux, with a modern interface,
  including the <b>Discord Flatpak</b>, with no manual configuration and no <code>sudo</code>.
</p>

<!-- Alt text (kept for when the screenshot returns): Presence page in dark theme -->
> 📷 Screenshot coming soon.

## Features

- **Works with any local Discord:** native (rpm/deb/tar.gz), **Flatpak**, Snap,
  Canary and Vesktop. The socket is found automatically, with no symbolic links to set up by hand.
- **Full editor:** details, state, elapsed time, images, up to 2 buttons and a party group,
  with **live preview** and field validation.
- **Presets:** save, search, rename and delete (with undo). To load one,
  just click the *Application ID* field.
- **Modern desktop look:** sidebar, top bar with per-page actions, search, empty states,
  notifications and dialogs.
- **Light, dark or system theme:** on KDE Plasma it follows the colour scheme and accent
  colour, and updates on its own when you switch the theme.
- **System tray**, keyboard shortcuts and a shortcut in the applications menu.
- **Standalone engine:** `discord_rpc_injector.py` uses only the standard library and can be
  imported into your own scripts.
- **Language selector:** Settings > Language switches the whole window between English and Brazilian Portuguese, live.

<!-- Alt text (kept for when the screenshot returns): Preset list shown when clicking the Application ID field -->
> 📷 Screenshot coming soon.

## Quick start

**1. Install PySide6** (6.5 or newer):

```bash
# Fedora
sudo dnf install python3-pyside6

# Ubuntu / Debian
sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtsvg

# Any distro, without touching the system
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

**2. Open the app:**

```bash
python3 main.py
```

**3. (Optional) Create the applications menu shortcut:**

```bash
python3 main.py --install-desktop
```

## How to use

1. Create an application at <https://discord.com/developers/applications>. Its name is what
   shows in "Playing …". Copy the **Application ID**.
2. With Discord open, paste the ID into the app and click **Connect**.
3. Fill in the fields and click **Apply** (Ctrl+Enter).

The full step-by-step guide, with images and buttons, is in
[Getting started](docs/02-getting-started.md).

## Compatibility

| Discord                    | Fedora and derivatives | Ubuntu / Debian |
|----------------------------|:----------------------:|:---------------:|
| Native (rpm, deb, tar.gz)  | ✅                     | ✅              |
| Flatpak (Flathub)          | ✅                     | ✅              |
| Snap                       | ✅                     | ✅              |

No `sudo` and no internet access are needed: the app only talks to Discord already open on
your computer and saves everything in folders under your user. Details in
[Compatibility](docs/05-compatibility.md).

## Documentation

| For users                                                | For developers                                          |
|----------------------------------------------------------|---------------------------------------------------------|
| [Installation](docs/01-installation.md)                    | [Architecture](docs/07-architecture.md)                  |
| [Getting started](docs/02-getting-started.md)           | [Development and tests](docs/08-development.md)     |
| [Using the app](docs/03-using-the-app.md)                 | [Engine reference](docs/09-engine-reference.md)      |
| [How it works](docs/04-how-it-works.md)                 |                                                         |
| [Compatibility](docs/05-compatibility.md)              |                                                         |
| [Troubleshooting](docs/06-troubleshooting.md)       |                                                         |

Full index: [docs/README.md](docs/README.md).

## Project structure

```
discord_rpc_injector.py   engine: IPC with Discord + presets (standard library only)
main.py                   opens the app; --install-desktop / --uninstall-desktop
rpc_ui/                   Qt interface: core/, theme/, widgets/, pages/
tests/                    automated tests (no windows, no real Discord)
docs/                     documentation
```

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

The tests cover startup, navigation, interaction with the interface and the engine,
including a server that simulates the socket of each type of Discord installation.

## Using only the engine

```python
from discord_rpc_injector import DiscordIPC

ipc = DiscordIPC("123456789012345678")
ipc.connect()
ipc.set_activity({"details": "Coding", "state": "Python"})
```

See the [Engine reference](docs/09-engine-reference.md).

## Your data

| File                                                   | Contents                         |
|--------------------------------------------------------|----------------------------------|
| `~/.config/discord-rpc-injector/presets.json`          | Presets                          |
| `~/.config/DiscordRPCInjector/DiscordRPCInjector.conf` | Preferences (theme, tray, language…)       |

The app does not use your Discord token or password.
