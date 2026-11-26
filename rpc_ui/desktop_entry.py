"""Gera e instala o atalho (.desktop) e o ícone para o usuário atual.

Os caminhos são calculados na hora (interpretador Python em uso, pasta do
projeto), então o mesmo código funciona em qualquer máquina, usuário ou venv.
Tudo é instalado em ``$XDG_DATA_HOME`` (padrão ``~/.local/share``), sem sudo.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from . import APP_ID, APP_NAME

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "main.py")
ICON_SVG = os.path.join(PROJECT_DIR, "rpc_icon.svg")
ICON_PNG = os.path.join(PROJECT_DIR, "rpc_icon.png")


def data_home() -> str:
    return os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")


def quote_exec_arg(arg: str) -> str:
    """Cita um argumento conforme a Desktop Entry Specification (chave Exec)."""
    arg = arg.replace("%", "%%")
    if not any(c in arg for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return arg
    escaped = "".join("\\" + c if c in '"`$\\' else c for c in arg)
    return f'"{escaped}"'


def render(python: str | None = None, main: str = MAIN_SCRIPT, workdir: str = PROJECT_DIR) -> str:
    python = python or sys.executable or "python3"
    exec_line = " ".join(quote_exec_arg(a) for a in (python, main))
    return "\n".join([
        "[Desktop Entry]",
        "Version=1.0",
        "Type=Application",
        f"Name={APP_NAME}",
        "GenericName=Rich Presence para Discord",
        "Comment=Define a presença (Rich Presence) do Discord, incluindo a versão Flatpak",
        f"Exec={exec_line}",
        f"Path={workdir}",
        f"Icon={APP_ID}",
        "Terminal=false",
        "Categories=Utility;",
        "Keywords=discord;rpc;rich;presence;status;",
        "StartupNotify=true",
        f"StartupWMClass={APP_ID}",
        "",
    ])


def paths(base: str | None = None) -> dict[str, str]:
    base = base or data_home()
    icons = os.path.join(base, "icons", "hicolor")
    return {
        "desktop": os.path.join(base, "applications", f"{APP_ID}.desktop"),
        "icon_svg": os.path.join(icons, "scalable", "apps", f"{APP_ID}.svg"),
        "icon_png": os.path.join(icons, "256x256", "apps", f"{APP_ID}.png"),
    }


def _refresh_caches(base: str) -> None:
    """Atualiza caches do menu/ícones quando as ferramentas existem (melhor esforço)."""
    cmds = [
        ["update-desktop-database", os.path.join(base, "applications")],
        ["gtk-update-icon-cache", "-q", "-t", os.path.join(base, "icons", "hicolor")],
        ["kbuildsycoca6"],
        ["kbuildsycoca5"],
    ]
    for cmd in cmds:
        if shutil.which(cmd[0]):
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def install(base: str | None = None, refresh: bool = True) -> list[str]:
    base = base or data_home()
    p = paths(base)
    written = []
    for key, src in (("icon_svg", ICON_SVG), ("icon_png", ICON_PNG)):
        if os.path.exists(src):
            os.makedirs(os.path.dirname(p[key]), exist_ok=True)
            shutil.copyfile(src, p[key])
            written.append(p[key])
    os.makedirs(os.path.dirname(p["desktop"]), exist_ok=True)
    with open(p["desktop"], "w", encoding="utf-8") as f:
        f.write(render())
    os.chmod(p["desktop"], 0o755)
    written.append(p["desktop"])
    if refresh:
        _refresh_caches(base)
    return written


def uninstall(base: str | None = None, refresh: bool = True) -> list[str]:
    base = base or data_home()
    removed = []
    for path in paths(base).values():
        if os.path.exists(path):
            os.remove(path)
            removed.append(path)
    if refresh:
        _refresh_caches(base)
    return removed
