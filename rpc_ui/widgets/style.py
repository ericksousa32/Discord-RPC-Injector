"""Helpers for dynamic properties used by the QSS."""

from PySide6.QtWidgets import QWidget


def set_prop(widget: QWidget, name: str, value) -> None:
    """Sets a property and forces the QSS to re-evaluate the selectors."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
