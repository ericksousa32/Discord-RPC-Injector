#!/usr/bin/env python3
"""
Motor do Discord RPC Injector para Linux.

Contém apenas a comunicação IPC com o Discord e a persistência das
predefinições. Usa somente a biblioteca padrão do Python e não precisa de
privilégios de administrador: tudo fica em pastas do próprio usuário.

Instalações do Discord suportadas (o socket é procurado nesta ordem):

* nativa (rpm, deb, tar.gz) e instâncias extras (PTB/Canary): ``discord-ipc-0..9``
  em ``$XDG_RUNTIME_DIR``;
* Flatpak (Discord, Canary e Vesktop): ``$XDG_RUNTIME_DIR/app/<id>/`` (socket
  exposto pelo lançador do Flathub) e ``$XDG_RUNTIME_DIR/.flatpak/<id>/xdg-run/``
  (Flatpak 1.15+);
* Snap: ``$XDG_RUNTIME_DIR/snap.discord/``;
* sem ``XDG_RUNTIME_DIR``: ``$TMPDIR``, ``$TMP``, ``$TEMP`` e ``/tmp``, como o
  próprio Discord faz.

A interface gráfica fica no pacote ``rpc_ui`` (inicie com ``main.py``).
"""

import os
import json
import struct
import socket
import tempfile
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# Predefinições
# ─────────────────────────────────────────────────────────────────────────────

APP_DIR_NAME = "discord-rpc-injector"


def config_dir() -> str:
    """Pasta de configuração do usuário (XDG), ex.: ``~/.config/discord-rpc-injector``."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_DIR_NAME)


PRESETS_FILE = os.path.join(config_dir(), "presets.json")


def load_presets() -> dict:
    """Lê as predefinições; arquivo ausente ou inválido resulta em ``{}``."""
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_presets(presets: dict):
    """Grava de forma atômica: uma falha no meio não corrompe o arquivo existente."""
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

# Apps Flatpak que expõem um servidor RPC compatível com o do Discord.
FLATPAK_IDS = (
    "com.discordapp.Discord",
    "com.discordapp.DiscordCanary",
    "dev.vencord.Vesktop",
)


class DiscordClosed(ConnectionError):
    """O Discord encerrou a conexão (opcode CLOSE), opcionalmente com código de erro."""

    def __init__(self, message: str, code=None):
        super().__init__(f"{message} (código {code})" if code is not None else message)
        self.code = code


class HandshakeRejected(ConnectionError):
    """O Discord respondeu, mas recusou a conexão (ex.: Application ID inválido)."""


class DiscordIPC:
    OP_HANDSHAKE = 0
    OP_FRAME     = 1
    OP_CLOSE     = 2

    # Segundos. O Discord costuma segurar o handshake por alguns segundos
    # quando conexões são abertas/fechadas em sequência rápida.
    CONNECT_TIMEOUT   = 2.0
    HANDSHAKE_TIMEOUT = 12.0
    IO_TIMEOUT        = 10.0

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.sock = None
        self.pid = os.getpid()

    # ── descoberta do socket ────────────────────────────────────────────────
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
        """Todos os caminhos candidatos, na ordem de preferência."""
        for base in self._search_dirs():
            for i in range(10):
                yield os.path.join(base, f"discord-ipc-{i}")

    def candidate_sockets(self):
        """Caminhos que existem, sem repetir o mesmo socket alcançado por links."""
        seen = set()
        for path in self._socket_paths():
            if not os.path.exists(path):
                continue
            real = os.path.realpath(path)
            if real in seen:
                continue
            seen.add(real)
            yield path

    # ── conexão ──────────────────────────────────────────────────────────────
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
                # Mesmo Discord atrás de outro caminho daria a mesma resposta.
                self._close_socket(sock)
                raise
            except socket.timeout:
                failures.append(f"{path}: o Discord não respondeu em "
                                f"{self.HANDSHAKE_TIMEOUT:.0f} s")
            except Exception as exc:
                failures.append(f"{path}: {exc}")
            self._close_socket(sock)

        if not failures:
            raise ConnectionError(
                "Socket do Discord não encontrado.\n"
                "Verifique se o Discord está aberto e tente novamente."
            )
        raise ConnectionError(
            "Não foi possível conectar ao Discord.\n" + "\n".join(failures)
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

    # ── protocolo ────────────────────────────────────────────────────────────
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
                raise ConnectionError("Conexão encerrada pelo Discord.")
            buf += chunk
        return buf

    def _recv(self):
        op, length = struct.unpack("<II", self._recv_exact(8))
        body = json.loads(self._recv_exact(length).decode("utf-8")) if length else {}
        if op == self.OP_CLOSE:
            raise DiscordClosed(body.get("message") or "Conexão encerrada pelo Discord.",
                                body.get("code"))
        return body

    def _handshake(self):
        self._send(self.OP_HANDSHAKE, {"v": 1, "client_id": self.client_id})
        try:
            resp = self._recv()
        except DiscordClosed as exc:
            # O Discord fecha com código quando recusa o handshake (ex.: 4000 = ID inválido).
            if exc.code is not None:
                raise HandshakeRejected(f"O Discord recusou a conexão: {exc}") from exc
            raise
        if resp.get("evt") not in ("READY", ""):
            raise HandshakeRejected(f"Handshake falhou: {resp}")

    def set_activity(self, activity):
        payload = {"cmd": "SET_ACTIVITY", "args": {"pid": self.pid, "activity": activity}, "nonce": str(uuid.uuid4())}
        self._send(self.OP_FRAME, payload)
        return self._recv()

    def clear_activity(self):
        payload = {"cmd": "SET_ACTIVITY", "args": {"pid": self.pid, "activity": None}, "nonce": str(uuid.uuid4())}
        self._send(self.OP_FRAME, payload)
        return self._recv()
