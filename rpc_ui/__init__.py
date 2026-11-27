"""Modern interface (Qt/PySide6) for the Discord RPC Injector.

The engine (``discord_rpc_injector.py``) does not depend on the interface: this package
only imports ``DiscordIPC``, ``load_presets`` and ``save_presets`` from it.
"""

APP_NAME = "Discord RPC Injector"
APP_ID = "discord-rpc-injector"
__version__ = "2.0.0"
