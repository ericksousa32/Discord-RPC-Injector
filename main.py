#!/usr/bin/env python3
"""Inicia o Discord RPC Injector (interface Qt sobre o motor ``discord_rpc_injector.py``).

Uso:
    python3 main.py                      abre o aplicativo
    python3 main.py --install-desktop    instala atalho e ícone no menu (sem sudo)
    python3 main.py --uninstall-desktop  remove atalho e ícone
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Discord RPC Injector")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--install-desktop", action="store_true",
                       help="instala o atalho e o ícone em ~/.local/share (sem sudo)")
    group.add_argument("--uninstall-desktop", action="store_true",
                       help="remove o atalho e o ícone instalados")
    args, qt_args = parser.parse_known_args()

    if args.install_desktop or args.uninstall_desktop:
        from rpc_ui import desktop_entry
        done = desktop_entry.install() if args.install_desktop else desktop_entry.uninstall()
        verb = "Instalado" if args.install_desktop else "Removido"
        for path in done:
            print(f"{verb}: {path}")
        if not done:
            print("Nada para remover.")
        return 0

    from rpc_ui.app import main as run_app
    return run_app([sys.argv[0], *qt_args])


if __name__ == "__main__":
    sys.exit(main())
