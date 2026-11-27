"""UI texts: ``tr(key, **values)`` returns the message from the active catalog.

Keys are stable (``area.subject``), so the code never depends on the displayed
text. Dynamic values appear as ``{name}`` placeholders in the catalog.
"""

from __future__ import annotations

from .en import MESSAGES


def tr(key: str, **values) -> str:
    text = MESSAGES.get(key, key)
    return text.format(**values) if values else text
