#!/usr/bin/env python3
"""Starts the Discord RPC Injector (Qt interface over the ``discord_rpc_injector.py`` engine).

Usage:
    python3 main.py                      opens the application
    python3 main.py --install-desktop    installs the menu shortcut and icon (no sudo)
    python3 main.py --uninstall-desktop  removes the shortcut and icon
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Discord RPC Injector")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install-desktop", action="store_true",
                       help="installs the shortcut and icon in ~/.local/share (no sudo)")
    group.add_argument("--uninstall-desktop", action="store_true",
                       help="removes the installed shortcut and icon")
    args, qt_args = parser.parse_known_args()

    if args.install_desktop or args.uninstall_desktop:
        from rpc_ui import desktop_entry
        done = desktop_entry.install() if args.install_desktop else desktop_entry.uninstall()
        verb = "Installed" if args.install_desktop else "Removed"
        for path in done:
            print(f"{verb}: {path}")
        if not done:
            print("Nothing to remove.")
        return 0

    from rpc_ui.app import main as run_app
    return run_app([sys.argv[0], *qt_args])


if __name__ == "__main__":
    sys.exit(main())
