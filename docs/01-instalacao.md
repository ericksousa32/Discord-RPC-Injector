# 1. Installation

> **Summary:** install PySide6, run `python3 main.py` and, if you want, create the menu
> shortcut with `python3 main.py --install-desktop`. None of this needs `sudo`, except
> installing packages through your distro's package manager.

## Requirements

| What       | Minimum version | For what                                             |
|------------|-----------------|------------------------------------------------------|
| Python     | 3.8             | Engine (uses only the standard library)              |
| PySide6    | 6.5             | Graphical interface (Qt)                             |
| Discord    | any             | Native, Flatpak or Snap, open and logged in          |

The engine works on its own, without PySide6. The interface needs PySide6 6.5 or newer
because it uses Qt's light/dark theme detection.

## Installing dependencies

### Fedora (and derivatives)

```bash
sudo dnf install python3-pyside6
```

### Ubuntu / Debian (and derivatives)

```bash
sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtsvg
```

Check the version with `python3 -c "import PySide6; print(PySide6.__version__)"`. If it is
older than 6.5, or the package does not exist in your distro version, use the venv below.

### Any distro, with a venv (without touching the system)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Then use `.venv/bin/python` instead of `python3` in the commands on this page.

## Opening the app

In the project folder:

```bash
python3 main.py
```

## Applications menu shortcut

```bash
python3 main.py --install-desktop
```

This creates the following, for your user only:

| File                                                                  | What it is           |
|-----------------------------------------------------------------------|----------------------|
| `~/.local/share/applications/discord-rpc-injector.desktop`            | Menu shortcut        |
| `~/.local/share/icons/hicolor/scalable/apps/discord-rpc-injector.svg` | Vector icon          |
| `~/.local/share/icons/hicolor/256x256/apps/discord-rpc-injector.png`  | PNG icon             |

The shortcut is generated with the Python **and** the folder used when the command runs.
So:

- if you **move the project folder**, run the command again;
- if you use a **venv**, run `.venv/bin/python main.py --install-desktop`, and the shortcut
  will open the app with the venv's Python.

To remove the shortcut and the icons:

```bash
python3 main.py --uninstall-desktop
```

## Where your data is

| File                                                     | Contents                                     |
|----------------------------------------------------------|----------------------------------------------|
| `~/.config/discord-rpc-injector/presets.json`            | Saved presets                                |
| `~/.config/DiscordRPCInjector/DiscordRPCInjector.conf`   | Preferences (theme, tray, language, last App ID)       |

Both respect `XDG_CONFIG_HOME`. To start from scratch, just delete these files.

---

Next: [Getting started](02-primeiros-passos.md)
