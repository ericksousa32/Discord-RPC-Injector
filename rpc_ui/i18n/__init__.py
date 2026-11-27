"""UI texts: ``tr(key, **values)`` returns the message from the active catalog.

Keys are stable (``area.subject``), so the code never depends on the displayed
text. Dynamic values appear as ``{name}`` placeholders in the catalog. English
is the default; a key missing from another catalog falls back to English.
"""

from __future__ import annotations

from .en import MESSAGES as _EN
from .pt_BR import MESSAGES as _PT_BR

DEFAULT_LANGUAGE = "en"
CATALOGS: dict[str, dict[str, str]] = {"en": _EN, "pt_BR": _PT_BR}

_active = {"code": DEFAULT_LANGUAGE, "messages": _EN}


def set_language(code: str) -> None:
    """Switch the catalog used by ``tr``. Raises ``ValueError`` for unknown codes."""
    if code not in CATALOGS:
        raise ValueError(f"unknown language: {code!r}")
    _active["code"] = code
    _active["messages"] = CATALOGS[code]


def current_language() -> str:
    return _active["code"]


def tr(key: str, **values) -> str:
    text = _active["messages"].get(key) or _EN.get(key, key)
    return text.format(**values) if values else text
