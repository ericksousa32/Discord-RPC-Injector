from __future__ import annotations

from PySide6.QtWidgets import QLabel

from .style import set_prop

_STATES = {
    "connected": ("ok", "● Conectado"),
    "connecting": ("busy", "◌ Conectando…"),
    "disconnected": ("off", "○ Desconectado"),
}


class StatusPill(QLabel):
    def __init__(self, state: str = "disconnected", parent=None):
        super().__init__(parent)
        self.setObjectName("StatusPill")
        self.set_state(state)

    def set_state(self, state: str) -> None:
        tone, text = _STATES.get(state, _STATES["disconnected"])
        self.state = state
        self.setText(text)
        set_prop(self, "tone", tone)
