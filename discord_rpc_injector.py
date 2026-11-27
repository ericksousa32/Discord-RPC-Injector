#!/usr/bin/env python3
"""
Discord RPC Injector engine for Linux.

Contains only the IPC communication with Discord and the persistence of
presets. It uses only the Python standard library and needs no administrator
privileges: everything lives in the user's own folders.

Supported Discord installs (the socket is searched for in this order):

* native (rpm, deb, tar.gz) and extra instances (PTB/Canary): ``discord-ipc-0..9``
  in ``$XDG_RUNTIME_DIR``;
* Flatpak (Discord, Canary and Vesktop): ``$XDG_RUNTIME_DIR/app/<id>/`` (socket
  exposed by the Flathub launcher) and ``$XDG_RUNTIME_DIR/.flatpak/<id>/xdg-run/``
  (Flatpak 1.15+);
* Snap: ``$XDG_RUNTIME_DIR/snap.discord/``;
* without ``XDG_RUNTIME_DIR``: ``$TMPDIR``, ``$TMP``, ``$TEMP`` and ``/tmp``, as
  Discord itself does.

The graphical interface lives in the ``rpc_ui`` package (start it with ``main.py``).
"""

import os
import json
import struct
import socket
import tempfile
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Presets
# ─────────────────────────────────────────────────────────────────────────────

APP_DIR_NAME = "discord-rpc-injector"


def config_dir() -> str:
    """User configuration folder (XDG), e.g. ``~/.config/discord-rpc-injector``."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_DIR_NAME)


PRESETS_FILE = os.path.join(config_dir(), "presets.json")


def load_presets() -> dict:
    """Reads the presets; a missing or invalid file yields ``{}``."""
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_presets(presets: dict):
    """Writes atomically: a failure midway does not corrupt the existing file."""
    folder = os.path.dirname(PRESETS_FILE)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".presets-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        os.replace(tmp, PRESETS_FILE)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Discord IPC Client
# ─────────────────────────────────────────────────────────────────────────────

# Flatpak apps that expose an RPC server compatible with Discord's.
FLATPAK_IDS = (
    "com.discordapp.Discord",
    "com.discordapp.DiscordCanary",
    "dev.vencord.Vesktop",
)


class DiscordClosed(ConnectionError):
    """Discord closed the connection (CLOSE opcode), optionally with an error code."""

    def __init__(self, message: str, code=None):
        super().__init__(f"{message} (code {code})" if code is not None else message)
        self.code = code


class HandshakeRejected(ConnectionError):
    """Discord answered but refused the connection (e.g. invalid Application ID)."""


class DiscordIPC:
    OP_HANDSHAKE = 0
    OP_FRAME     = 1
    OP_CLOSE     = 2

    # Seconds. Discord often holds the handshake for a few seconds
    # when connections are opened and closed in quick succession.
    CONNECT_TIMEOUT   = 2.0
    HANDSHAKE_TIMEOUT = 12.0
    IO_TIMEOUT        = 10.0

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.sock = None
        self.pid = os.getpid()

    # ── socket discovery ────────────────────────────────────────────────
    @staticmethod
    def _search_dirs():
        runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        dirs = [runtime]
        for app_id in FLATPAK_IDS:
            dirs.append(os.path.join(runtime, "app", app_id))
            dirs.append(os.path.join(runtime, ".flatpak", app_id, "xdg-run"))
        dirs.append(os.path.join(runtime, "snap.discord"))
        for var in ("TMPDIR", "TMP", "TEMP"):
            if os.environ.get(var):
                dirs.append(os.environ[var])
        dirs.append("/tmp")
        seen, unique = set(), []
        for d in dirs:
            d = os.path.normpath(d)
            if d not in seen:
                seen.add(d)
                unique.append(d)
        return unique

    def _socket_paths(self):
        """All candidate paths, in order of preference."""
        for base in self._search_dirs():
            for i in range(10):
                yield os.path.join(base, f"discord-ipc-{i}")

    def candidate_sockets(self):
        """Paths that exist, without repeating the same socket reached through links."""
        seen = set()
        for path in self._socket_paths():
            if not os.path.exists(path):
                continue
            real = os.path.realpath(path)
            if real in seen:
                continue
            seen.add(real)
            yield path

    # ── connection ──────────────────────────────────────────────────────────────
    def connect(self):
        failures = []
        for path in self.candidate_sockets():
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.settimeout(self.CONNECT_TIMEOUT)
                sock.connect(path)
                sock.settimeout(self.HANDSHAKE_TIMEOUT)
                self.sock = sock
                self._handshake()
                sock.settimeout(self.IO_TIMEOUT)
                return path
            except HandshakeRejected:
                # The same Discord behind another path would give the same answer.
                self._close_socket(sock)
                raise
            except socket.timeout:
                failures.append(f"{path}: Discord did not respond within "
                                f"{self.HANDSHAKE_TIMEOUT:.0f} s")
            except Exception as exc:
                failures.append(f"{path}: {exc}")
            self._close_socket(sock)

        if not failures:
            raise ConnectionError(
                "Discord socket not found.\n"
                "Make sure Discord is open and try again."
            )
        raise ConnectionError(
            "Could not connect to Discord.\n" + "\n".join(failures)
        )

    def _close_socket(self, sock):
        try:
            sock.close()
        except OSError:
            pass
        if self.sock is sock:
            self.sock = None

    def disconnect(self):
        if self.sock:
            try:
                self._send(self.OP_CLOSE, {})
            except Exception:
                pass
            self._close_socket(self.sock)

    # ── protocol ────────────────────────────────────────────────────────────
    def _encode(self, opcode, payload):
        data = json.dumps(payload).encode("utf-8")
        return struct.pack("<II", opcode, len(data)) + data

    def _send(self, opcode, payload):
        self.sock.sendall(self._encode(opcode, payload))

    def _recv_exact(self, size):
        buf = b""
        while len(buf) < size:
            chunk = self.sock.recv(size - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed by Discord.")
            buf += chunk
        return buf

    def _recv(self):
        op, length = struct.unpack("<II", self._recv_exact(8))
        body = json.loads(self._recv_exact(length).decode("utf-8")) if length else {}
        if op == self.OP_CLOSE:
            raise DiscordClosed(body.get("message") or "Connection closed by Discord.",
                                body.get("code"))
        return body

    def _handshake(self):
        self._send(self.OP_HANDSHAKE, {"v": 1, "client_id": self.client_id})
        try:
            resp = self._recv()
        except DiscordClosed as exc:
            # Discord closes with a code when it refuses the handshake (e.g. 4000 = invalid ID).
            if exc.code is not None:
                raise HandshakeRejected(f"Discord refused the connection: {exc}") from exc
            raise
        if resp.get("evt") not in ("READY", ""):
            raise HandshakeRejected(f"Handshake failed: {resp}")

    def set_activity(self, activity):
        payload = {"cmd": "SET_ACTIVITY", "args": {"pid": self.pid, "activity": activity}, "nonce": str(uuid.uuid4())}
        self._send(self.OP_FRAME, payload)
        return self._recv()

    def clear_activity(self):
        payload = {"cmd": "SET_ACTIVITY", "args": {"pid": self.pid, "activity": None}, "nonce": str(uuid.uuid4())}
        self._send(self.OP_FRAME, payload)
        return self._recv()
