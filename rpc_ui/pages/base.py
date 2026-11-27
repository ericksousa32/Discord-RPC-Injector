from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from ..i18n import tr


class Page(QWidget):
    """Page contract: metadata for the top bar and optional search."""

    key = ""
    title_key = ""  # catalog key for the title
    icon = ""
    search_placeholder: str | None = None  # None = page without search

    header_changed = Signal()  # subtitle/actions changed

    @property
    def title(self) -> str:
        return tr(self.title_key)

    def subtitle(self) -> str:
        return ""

    def header_actions(self) -> list[QWidget]:
        return []

    def set_filter(self, text: str) -> None:
        pass

    def activated(self) -> None:
        """Called when the page is shown."""

    def retranslate(self) -> None:
        """Re-apply every text after the language changes."""
