"""Ajudantes para propriedades dinâmicas usadas pelo QSS."""

from PySide6.QtWidgets import QWidget


def set_prop(widget: QWidget, name: str, value) -> None:
    """Define uma propriedade e força o QSS a reavaliar os seletores."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
