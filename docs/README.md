# Discord RPC Injector documentation

Welcome! This folder has everything you need to **use**, **understand** and **modify**
Discord RPC Injector. Each file covers one topic and can be read on its own.

## Where to start?

| I want to…                                        | Read                                                   |
|---------------------------------------------------|--------------------------------------------------------|
| Install and open the app                          | [Installation](01-installation.md)                       |
| Show my first presence on Discord                 | [Getting started](02-getting-started.md)              |
| Learn about each screen, shortcut and option      | [Using the app](03-using-the-app.md)                    |
| Understand how the app talks to Discord           | [How it works](04-how-it-works.md)                    |
| Check whether it works on my distro/installation  | [Compatibility](05-compatibility.md)                 |
| Solve a problem                                   | [Troubleshooting](06-troubleshooting.md)          |
| Understand how the code is organised              | [Architecture](07-architecture.md)                      |
| Run the tests or contribute code                  | [Development](08-development.md)                   |
| Use the engine in another Python script           | [Engine reference](09-engine-reference.md)          |

## The modules

**For users**

1. [Installation](01-installation.md): dependencies on Fedora, Ubuntu or a venv, and the menu shortcut.
2. [Getting started](02-getting-started.md): from the Developer Portal to the presence showing on your profile.
3. [Using the app](03-using-the-app.md): pages, presets, keyboard shortcuts, theme and tray.

**For those who want to understand**

4. [How it works](04-how-it-works.md): Discord's IPC socket explained simply.
5. [Compatibility](05-compatibility.md): native, Flatpak and Snap Discord; Fedora and Ubuntu; no sudo.
6. [Troubleshooting](06-troubleshooting.md): common symptoms and how to fix them.

**For developers**

7. [Architecture](07-architecture.md): layers, folders and data flow.
8. [Development](08-development.md): tests, creating pages and widgets, theme.
9. [Engine reference](09-engine-reference.md): API of `discord_rpc_injector.py`.

## Quick glossary

- **Rich Presence (RPC):** the "Playing…" card that shows on your Discord profile.
- **Application ID:** the number that identifies the "application" created in the Discord
  Developer Portal. The name of that application is what appears in "Playing **…**".
- **IPC socket:** a special file (`discord-ipc-0`) through which local programs talk to the
  Discord open on your computer.
- **Preset:** a set of fields saved under a name, to be reused later.
- **Engine:** the `discord_rpc_injector.py` file, which talks to Discord. The graphical
  interface lives in the `rpc_ui/` package.
