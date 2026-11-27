# 5. Compatibility

> **Summary:** works with native, Flatpak and Snap Discord, on distros based on Fedora and
> Ubuntu, without `sudo` and without manual socket configuration.

## Discord installations

| Installation                            | Support | Note                                                 |
|-----------------------------------------|:-------:|------------------------------------------------------|
| Native: rpm, deb, tar.gz                | ✅      | Socket in `$XDG_RUNTIME_DIR`                         |
| Native PTB / Canary (2nd instance)      | ✅      | `discord-ipc-1` … `-9`                               |
| Flatpak `com.discordapp.Discord`        | ✅      | Uses the socket created by the Flathub launcher      |
| Flatpak `com.discordapp.DiscordCanary`  | ✅      |                                                      |
| Flatpak Vesktop `dev.vencord.Vesktop`   | ✅*     | Depends on the RPC server (arRPC) being active in Vesktop |
| Snap `discord`                          | ✅      | Socket in `snap.discord/`                            |
| Discord in the browser                  | ❌      | The browser does not open an IPC socket              |

\* Covered by the automated tests with a simulated Discord, but not verified with the real
Vesktop.

> ℹ️ The behaviour with the **Discord Flatpak** was verified with the real Discord. The other
> formats are covered by automated tests that simulate the socket exactly where each
> installation creates it (see [Development](08-desenvolvimento.md#running-the-tests)).

## Distributions

| Family                   | Engine | Interface                                                       |
|--------------------------|:------:|-----------------------------------------------------------------|
| Fedora and derivatives   | ✅     | `python3-pyside6` from the repositories                         |
| Ubuntu / Debian          | ✅     | `python3-pyside6.*` if it is 6.5 or newer; otherwise venv + pip |
| Others (Arch, openSUSE…) | ✅     | The distro's PySide6 package, or venv + pip                     |

The **engine** uses only the standard library of Python 3.8+, so it runs on any distro. The
**interface** needs PySide6 6.5 or newer. See [Installation](01-instalacao.md).

## Desktop environments

| Feature                        | KDE Plasma               | GNOME                              | Others                  |
|--------------------------------|--------------------------|------------------------------------|-------------------------|
| "System" theme                 | KDE colours and accent   | Qt palette and light/dark mode     | Qt palette              |
| System tray                    | ✅                       | Only with the AppIndicator extension | Depends on the panel  |
| Icon in the bar (Wayland)      | ✅ with the shortcut installed | ✅ with the shortcut installed | ✅ with the shortcut installed |

Without a tray available, closing the window simply quits the app.

## Permissions: is sudo needed?

**No.** Everything the app reads or writes belongs to your user:

| Resource                    | Location                                      | Owner         |
|-----------------------------|-----------------------------------------------|---------------|
| Discord socket              | `/run/user/<uid>/…`                           | you           |
| Presets                     | `~/.config/discord-rpc-injector/`             | you           |
| Preferences                 | `~/.config/DiscordRPCInjector/`               | you           |
| Shortcut and icon           | `~/.local/share/…`                            | you           |

> ⚠️ **Do not run the app with `sudo`.** As root, it would look for the socket in the root
> folder (`/run/user/0`) and would not find the Discord of your user.

SELinux (Fedora) and AppArmor (Ubuntu) do not block the connection: the app runs outside a
sandbox, with the same permissions as you.

## If the app itself is packaged as a Flatpak

Today the app runs directly on the system. If it is ever packaged as a Flatpak, it will need
permission to see the Discord socket, for example
`--filesystem=xdg-run/app/com.discordapp.Discord:ro` and `--filesystem=xdg-run/discord-ipc-0:ro`.

---

Previous: [How it works](04-como-funciona.md) · Next: [Troubleshooting](06-solucao-de-problemas.md)
