# 9. Engine reference

> **Summary:** `discord_rpc_injector.py` is a self-contained module (standard library only)
> that you can import into any Python script to set the Discord presence.

## Quick example

```python
import time
from discord_rpc_injector import DiscordIPC

ipc = DiscordIPC("1234567890123456789")      # your Application ID
print("Connected via", ipc.connect())

ipc.set_activity({
    "details": "Writing documentation",
    "state": "In the terminal",
    "timestamps": {"start": int(time.time())},
})

input("Press Enter to remove the presence…")
ipc.clear_activity()
ipc.disconnect()
```

## `DiscordIPC(client_id)`

Client for Discord's local IPC protocol.

| Member                     | Description                                                              |
|----------------------------|--------------------------------------------------------------------------|
| `connect() -> str`         | Finds the socket, does the handshake and returns the path used           |
| `set_activity(activity)`   | Sends `SET_ACTIVITY` with the given dictionary; returns Discord's response |
| `clear_activity()`         | Removes the presence (`activity = null`)                                 |
| `disconnect()`             | Sends `CLOSE` and closes the socket (safe to call more than once)        |
| `candidate_sockets()`      | Generator with the existing sockets, in order and without repeats        |
| `sock`                     | The open `socket.socket`, or `None`                                      |
| `pid`                      | PID sent to Discord (that of the current process)                        |

### Timeouts (class attributes, in seconds)

| Attribute           | Default | When                                      |
|---------------------|--------:|-------------------------------------------|
| `CONNECT_TIMEOUT`   | 2.0     | Opening the connection to each socket     |
| `HANDSHAKE_TIMEOUT` | 12.0    | Waiting for `READY`                       |
| `IO_TIMEOUT`        | 10.0    | Each send/response after connecting       |

To change them, create a subclass:

```python
class FastIPC(DiscordIPC):
    HANDSHAKE_TIMEOUT = 3.0
```

### Errors

| Exception                         | When                                                                        |
|-----------------------------------|-----------------------------------------------------------------------------|
| `ConnectionError`                 | No socket found, or none responded (the message lists each path and the reason) |
| `HandshakeRejected`               | Discord refused the handshake (e.g. code 4000, invalid ID)                  |
| `DiscordClosed`                   | Discord closed the connection; `code` attribute with the code, if any       |
| `socket.timeout` / `TimeoutError` | A response took longer than `IO_TIMEOUT` after connecting                   |

`HandshakeRejected` and `DiscordClosed` are subclasses of `ConnectionError`.

## Format of `activity`

All fields are optional. The main ones:

```python
{
    "details": str,                       # 1st line
    "state": str,                         # 2nd line
    "timestamps": {"start": int},         # epoch in seconds → "elapsed"
    "assets": {
        "large_image": str, "large_text": str,   # Art Asset key + tooltip
        "small_image": str, "small_text": str,
    },
    "buttons": [{"label": str, "url": str}],     # up to 2
    "party": {"id": str, "size": [current, max]},
}
```

## Presets

| Name                        | Description                                                        |
|-----------------------------|--------------------------------------------------------------------|
| `config_dir() -> str`       | `$XDG_CONFIG_HOME/discord-rpc-injector` (default `~/.config/…`)    |
| `PRESETS_FILE`              | Path of `presets.json`                                             |
| `load_presets() -> dict`    | Reads the presets; a missing or invalid file results in `{}`       |
| `save_presets(presets)`     | Writes atomically (creates the folder if needed)                   |

Format of `presets.json`: an object whose keys are the preset names:

```json
{
  "Fedora": {
    "app_id": "123456789012345678",
    "details": "Just Chilling",
    "state": "(KDE Plasma)",
    "large_key": "", "large_text": "", "small_key": "", "small_text": "",
    "btn1_label": "", "btn1_url": "", "btn2_label": "", "btn2_url": "",
    "party_size": "", "party_max": "", "party_id": "",
    "show_elapsed": true
  }
}
```

## Other constants

| Name           | Description                                                             |
|----------------|-------------------------------------------------------------------------|
| `FLATPAK_IDS`  | Flatpak IDs whose sockets are looked up (Discord, Canary, Vesktop)      |
| `APP_DIR_NAME` | Name of the configuration folder (`discord-rpc-injector`)               |

To support another Flatpak client, just add its ID to `FLATPAK_IDS`.

---

Previous: [Development](08-desenvolvimento.md) · [Back to index](README.md)
