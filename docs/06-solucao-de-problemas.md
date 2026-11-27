# 6. Troubleshooting

> **General tip:** the **Log** page shows each step of the connection and the full error
> message. Start there.

## "Discord socket not found"

The app did not find any `discord-ipc-*` in the known locations.

1. Is Discord **open and logged in**? (Being open in the browser is not enough.)
2. List the existing sockets:

   ```bash
   find "$XDG_RUNTIME_DIR" /tmp -maxdepth 4 -name 'discord-ipc-*' 2>/dev/null
   ```

3. If the command shows nothing, quit Discord **completely** (including from the tray) and
   open it again.
4. If the socket is in a place outside the list in
   [How it works](04-como-funciona.md#1-finding-the-socket), open an issue with the path.

## "Discord refused the connection: Invalid Client ID (code 4000)"

The Application ID does not exist or was mistyped. Copy it again from
<https://discord.com/developers/applications> → your application → **Application ID**.

## "Discord did not respond in 12 s" or it takes a long time to connect

Discord sometimes holds new connections for a few seconds, especially after connecting and
disconnecting several times in a row.

- Wait about 10 seconds and click **Connect** again.
- If it happens every time, restart Discord.

## Connects, but the presence does not show

- Check the **Discord settings**: *Activity → Activity Privacy →* "Share your activity" must be
  turned on.
- The **Invisible** status hides the activity.
- Discord can take a few seconds to update the profile.

## The images do not show

- The **key** must match exactly the name of the asset in *Rich Presence → Art Assets*.
- Newly uploaded assets can take a few minutes to become available.

## The buttons do not show

Discord usually does not show the buttons **to the user themselves**. Ask someone to check your
profile. Each button needs a label **and** a URL (`http://` or `https://`).

## I closed the window and the app is still running

This is the **"Keep in the system tray when the window is closed"** option (Settings page).
Use **Ctrl+Q** or **Quit** in the tray menu to close it for good.

## The menu shortcut does not open the app

The project folder was probably moved, or the Python changed (e.g. a new venv). Generate the
shortcut again:

```bash
python3 main.py --install-desktop
```

## "ModuleNotFoundError: No module named 'PySide6'" or a Qt version error

Install or update PySide6 (it must be 6.5 or newer). See
[Installation](01-instalacao.md#installing-dependencies).

## The theme does not follow KDE

In **Settings → Appearance**, select **System**. The app reads `~/.config/kdeglobals`; if the
file does not exist (outside KDE), it uses the Qt palette.

---

Previous: [Compatibility](05-compatibilidade.md) · Next: [Architecture](07-arquitetura.md)
