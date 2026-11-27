from __future__ import annotations

from PySide6.QtWidgets import QLabel

from ..i18n import tr
from .style import set_prop

# state → (visual tone, symbol, text key)
_STATES = {
    "connected": ("ok", "●", "status.connected"),
    "connecting": ("busy", "◌", "status.connecting"),
    "disconnected": ("off", "○", "status.disconnected"),
}


def state_label(state: str) -> str:
    """Short state text without the symbol (e.g. ``Connected``)."""
    return tr(_STATES.get(state, _STATES["disconnected"])[2])


class StatusPill(QLabel):
    def __init__(self, state: str = "disconnected", parent=None):
        super().__init__(parent)
        self.setObjectName("StatusPill")
        self.set_state(state)

    def set_state(self, state: str) -> None:
        tone, glyph, _ = _STATES.get(state, _STATES["disconnected"])
        self.state = state
        self.setText(f"{glyph} {state_label(state)}")
        set_prop(self, "tone", tone)
