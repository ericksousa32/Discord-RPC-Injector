"""Motor: descoberta do socket em cada tipo de instalação, protocolo, tempos limite,
predefinições e atalho. Usa um servidor que imita o Discord; não toca no Discord real
nem nos arquivos do usuário."""

import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from tests.helpers import ROOT

import discord_rpc_injector as eng
from rpc_ui import desktop_entry


# ── Discord falso ───────────────────────────────────────────────────────────

class FakeDiscord:
    """Servidor IPC mínimo. ``mode``: ready | delay | reject | silent."""

    def __init__(self, path, mode="ready", delay=0.0):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path, self.mode, self.delay = path, mode, delay
        self.frames = []          # (opcode, payload) recebidos
        self.connections = 0
        self.srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.srv.bind(path)
        self.srv.listen(4)
        self.srv.settimeout(5)
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    def _read(self, c):
        head = b""
        while len(head) < 8:
            chunk = c.recv(8 - len(head))
            if not chunk:
                return None
            head += chunk
        op, n = struct.unpack("<II", head)
        body = b""
        while len(body) < n:
            body += c.recv(n - len(body))
        return op, json.loads(body or b"{}")

    @staticmethod
    def _send(c, op, payload):
        data = json.dumps(payload).encode()
        c.sendall(struct.pack("<II", op, len(data)) + data)

    def _serve(self):
        while not self._stop:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            self.connections += 1
            with c:
                msg = self._read(c)
                if msg is None:
                    continue
                self.frames.append(msg)
                if self.mode == "silent":
                    time.sleep(2)
                    continue
                if self.mode == "reject":
                    self._send(c, 2, {"code": 4000, "message": "Invalid Client ID"})
                    continue
                time.sleep(self.delay)
                self._send(c, 1, {"cmd": "DISPATCH", "evt": "READY", "data": {"v": 1}})
                while (msg := self._read(c)) is not None:
                    self.frames.append(msg)
                    op, payload = msg
                    if op == 2:
                        break
                    self._send(c, 1, {"cmd": payload.get("cmd"), "evt": None,
                                      "nonce": payload.get("nonce"), "data": {}})

    def close(self):
        self._stop = True
        self.srv.close()


class FastIPC(eng.DiscordIPC):
    CONNECT_TIMEOUT = 0.5
    HANDSHAKE_TIMEOUT = 0.6
    IO_TIMEOUT = 0.6


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        base = "/tmp/claude-1000" if os.path.isdir("/tmp/claude-1000") else None
        self.tmp = tempfile.mkdtemp(prefix="rpc-", dir=base)   # caminho curto (limite AF_UNIX)
        self.runtime = os.path.join(self.tmp, "rt")
        self.tmpdir = os.path.join(self.tmp, "tmp")
        os.makedirs(self.runtime)
        os.makedirs(self.tmpdir)
        self.servers = []
        env = {k: v for k, v in os.environ.items() if k not in ("TMPDIR", "TMP", "TEMP")}
        env["XDG_RUNTIME_DIR"] = self.runtime
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()
        # Isola do sistema real: só existem caminhos dentro da pasta do teste.
        real_exists = os.path.exists
        self._exists = mock.patch.object(
            eng.os.path, "exists",
            lambda p: str(p).startswith(self.tmp) and real_exists(p))
        self._exists.start()

    def tearDown(self):
        self._exists.stop()
        self._env.stop()
        for s in self.servers:
            s.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def serve(self, rel, mode="ready", delay=0.0, root=None):
        s = FakeDiscord(os.path.join(root or self.runtime, rel), mode, delay)
        self.servers.append(s)
        return s


# ── descoberta do socket ────────────────────────────────────────────────────

class DiscoveryTests(EngineTestCase):
    LAYOUTS = [
        ("nativo (rpm/deb/tar.gz)", "discord-ipc-0"),
        ("segunda instância nativa", "discord-ipc-1"),
        ("Flatpak Flathub (socat do lançador)", "app/com.discordapp.Discord/discord-ipc-0"),
        ("Flatpak 1.15+ xdg-run por app", ".flatpak/com.discordapp.Discord/xdg-run/discord-ipc-0"),
        ("Flatpak Canary", "app/com.discordapp.DiscordCanary/discord-ipc-0"),
        ("Vesktop Flatpak", "app/dev.vencord.Vesktop/discord-ipc-0"),
        ("Snap", "snap.discord/discord-ipc-0"),
    ]

    def test_each_install_layout_is_found(self):
        for label, rel in self.LAYOUTS:
            with self.subTest(label):
                server = self.serve(rel)
                ipc = FastIPC("123")
                try:
                    self.assertEqual(ipc.connect(), server.path)
                    self.assertEqual(server.frames[0], (0, {"v": 1, "client_id": "123"}))
                finally:
                    ipc.disconnect()
                    server.close()
                    os.remove(server.path)

    def test_tmpdir_fallback_without_xdg_runtime_dir(self):
        del os.environ["XDG_RUNTIME_DIR"]
        os.environ["TMPDIR"] = self.tmpdir
        server = self.serve("discord-ipc-0", root=self.tmpdir)
        ipc = FastIPC("123")
        self.assertEqual(ipc.connect(), server.path)
        ipc.disconnect()

    def test_search_dirs_order_and_fallbacks(self):
        os.environ["TMPDIR"] = self.tmpdir     # mesma prioridade do Discord: TMPDIR, TMP, TEMP
        os.environ["TMP"] = "/tmp/"            # duplicado de /tmp: aparece uma vez
        dirs = eng.DiscordIPC._search_dirs()
        rt = self.runtime
        self.assertEqual(dirs[:3], [rt, f"{rt}/app/com.discordapp.Discord",
                                    f"{rt}/.flatpak/com.discordapp.Discord/xdg-run"])
        self.assertIn(f"{rt}/snap.discord", dirs)
        self.assertLess(dirs.index(self.tmpdir), dirs.index("/tmp"))
        self.assertEqual(dirs.count("/tmp"), 1)

    def test_default_runtime_dir_when_unset(self):
        del os.environ["XDG_RUNTIME_DIR"]
        self.assertEqual(eng.DiscordIPC._search_dirs()[0], f"/run/user/{os.getuid()}")

    def test_symlink_to_same_socket_is_tried_once(self):
        server = self.serve("app/com.discordapp.Discord/discord-ipc-0")
        os.symlink("app/com.discordapp.Discord/discord-ipc-0",
                   os.path.join(self.runtime, "discord-ipc-0"))
        self.assertEqual(len(list(eng.DiscordIPC("1").candidate_sockets())), 1)
        self.assertEqual(server.connections, 0)

    def test_no_socket_found(self):
        with self.assertRaisesRegex(ConnectionError, "não encontrado"):
            FastIPC("123").connect()


# ── robustez da conexão ─────────────────────────────────────────────────────

class ConnectionRobustnessTests(EngineTestCase):
    def test_silent_socket_times_out_and_next_path_is_used(self):
        silent = self.serve("discord-ipc-0", mode="silent")
        good = self.serve("app/com.discordapp.Discord/discord-ipc-0")
        ipc = FastIPC("123")
        t = time.monotonic()
        self.assertEqual(ipc.connect(), good.path)
        self.assertLess(time.monotonic() - t, 3)
        self.assertEqual(silent.connections, 1)
        ipc.disconnect()

    def test_slow_handshake_within_timeout_succeeds(self):
        # O Discord segura o handshake por alguns segundos após reconexões rápidas.
        server = self.serve("discord-ipc-0", delay=0.3)
        ipc = FastIPC("123")
        self.assertEqual(ipc.connect(), server.path)
        ipc.disconnect()

    def test_all_paths_silent_reports_timeout(self):
        self.serve("discord-ipc-0", mode="silent")
        with self.assertRaisesRegex(ConnectionError, "não respondeu"):
            FastIPC("123").connect()

    def test_rejected_handshake_stops_immediately(self):
        self.serve("discord-ipc-0", mode="reject")
        other = self.serve("app/com.discordapp.Discord/discord-ipc-0")
        with self.assertRaises(eng.HandshakeRejected) as ctx:
            FastIPC("999").connect()
        self.assertIn("4000", str(ctx.exception))
        self.assertEqual(other.connections, 0)

    def test_stale_socket_file_is_skipped(self):
        stale = os.path.join(self.runtime, "discord-ipc-0")
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(stale)
        s.close()                                   # arquivo fica, ninguém escuta
        good = self.serve("discord-ipc-1")
        ipc = FastIPC("123")
        self.assertEqual(ipc.connect(), good.path)
        ipc.disconnect()

    def test_activity_round_trip_and_close(self):
        server = self.serve("discord-ipc-0")
        ipc = FastIPC("123")
        ipc.connect()
        ipc.set_activity({"details": "Teste"})
        ipc.clear_activity()
        ipc.disconnect()
        time.sleep(0.1)
        ops = [op for op, _ in server.frames]
        self.assertEqual(ops, [0, 1, 1, 2])
        self.assertEqual(server.frames[1][1]["args"]["activity"], {"details": "Teste"})
        self.assertIsNone(server.frames[2][1]["args"]["activity"])
        self.assertIsNone(ipc.sock)


# ── predefinições ───────────────────────────────────────────────────────────

class PresetStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.file = os.path.join(self.tmp, "cfg", "discord-rpc-injector", "presets.json")
        self._patch = mock.patch.object(eng, "PRESETS_FILE", self.file)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_config_dir_follows_xdg(self):
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/x/cfg"}):
            self.assertEqual(eng.config_dir(), "/x/cfg/discord-rpc-injector")

    def test_round_trip_creates_folder(self):
        self.assertEqual(eng.load_presets(), {})
        eng.save_presets({"Ação": {"details": "olá"}})
        self.assertEqual(eng.load_presets(), {"Ação": {"details": "olá"}})
        self.assertEqual(os.listdir(os.path.dirname(self.file)), ["presets.json"])  # sem temporários

    def test_corrupt_file_returns_empty(self):
        os.makedirs(os.path.dirname(self.file))
        with open(self.file, "w") as f:
            f.write("{quebrado")
        self.assertEqual(eng.load_presets(), {})

    def test_failed_save_keeps_previous_file(self):
        eng.save_presets({"A": {}})
        with self.assertRaises(TypeError):
            eng.save_presets({"B": object()})        # não serializável
        self.assertEqual(eng.load_presets(), {"A": {}})
        self.assertEqual(os.listdir(os.path.dirname(self.file)), ["presets.json"])


class EngineModuleTests(unittest.TestCase):
    def test_engine_uses_only_standard_library(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); before = set(sys.modules); "
                "import discord_rpc_injector; "
                "extra = {m.split('.')[0] for m in set(sys.modules) - before} - {'discord_rpc_injector'}; "
                "print(','.join(sorted(m for m in extra if m not in sys.stdlib_module_names)))")
        out = subprocess.run([sys.executable, "-c", code, ROOT], capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertEqual(out, "")

    def test_engine_public_api(self):
        for name in ("DiscordIPC", "load_presets", "save_presets", "PRESETS_FILE",
                     "HandshakeRejected", "FLATPAK_IDS", "config_dir"):
            self.assertTrue(hasattr(eng, name), name)
        self.assertFalse(hasattr(eng, "App"))

    def test_frame_encoding(self):
        ipc = eng.DiscordIPC("123")
        frame = ipc._encode(ipc.OP_HANDSHAKE, {"v": 1, "client_id": "123"})
        op, length = struct.unpack("<II", frame[:8])
        self.assertEqual((op, json.loads(frame[8:8 + length])), (0, {"v": 1, "client_id": "123"}))


# ── atalho (.desktop) ───────────────────────────────────────────────────────

class DesktopEntryTests(unittest.TestCase):
    def test_exec_quoting(self):
        q = desktop_entry.quote_exec_arg
        self.assertEqual(q("/usr/bin/python3"), "/usr/bin/python3")
        self.assertEqual(q("/home/a b/main.py"), '"/home/a b/main.py"')
        self.assertEqual(q('/x/"$y`\\/100%'), '"/x/\\"\\$y\\`\\\\/100%%"')

    def test_render_uses_current_interpreter_and_project(self):
        text = desktop_entry.render()
        self.assertIn(f"Exec={desktop_entry.quote_exec_arg(sys.executable)} ", text)
        self.assertIn(desktop_entry.MAIN_SCRIPT, text)
        self.assertIn("Icon=discord-rpc-injector", text)
        self.assertIn(f"Path={desktop_entry.PROJECT_DIR}", text)

    def test_install_and_uninstall_in_custom_base(self):
        base = tempfile.mkdtemp()
        try:
            written = desktop_entry.install(base, refresh=False)
            paths = desktop_entry.paths(base)
            self.assertIn(paths["desktop"], written)
            self.assertTrue(os.path.exists(paths["icon_svg"]))
            validator = shutil.which("desktop-file-validate")
            if validator:
                r = subprocess.run([validator, paths["desktop"]], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            removed = desktop_entry.uninstall(base, refresh=False)
            self.assertEqual(sorted(removed), sorted(written))
            self.assertFalse(os.path.exists(paths["desktop"]))
        finally:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
