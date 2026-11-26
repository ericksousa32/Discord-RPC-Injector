from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget


class Page(QWidget):
    """Contrato de uma página: metadados para a barra superior e busca opcional."""

    key = ""
    title = ""
    icon = ""
    search_placeholder: str | None = None  # None = página sem busca

    header_changed = Signal()  # subtítulo/ações mudaram

    def subtitle(self) -> str:
        return ""

    def header_actions(self) -> list[QWidget]:
        return []

    def set_filter(self, text: str) -> None:
        pass

    def activated(self) -> None:
        """Chamado quando a página passa a ser exibida."""
