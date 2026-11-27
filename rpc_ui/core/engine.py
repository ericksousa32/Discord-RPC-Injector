"""Adapter for the engine (``discord_rpc_injector.py``).

Every access to the engine goes through here, so the rest of the interface
does not depend on the module's details.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import discord_rpc_injector as _engine  # noqa: E402

DiscordIPC = _engine.DiscordIPC
load_presets = _engine.load_presets
save_presets = _engine.save_presets
PROJECT_DIR = _ROOT
PRESETS_FILE = _engine.PRESETS_FILE
ICON_PATH = os.path.join(PROJECT_DIR, "rpc_icon.png")
ICON_SVG_PATH = os.path.join(PROJECT_DIR, "rpc_icon.svg")
