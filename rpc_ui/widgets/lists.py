"""Helpers for QListWidget rows that are built from widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QListWidget


def clear_list(list_widget: QListWidget) -> None:
    """Empty the list and delete its row widgets.

    ``QListWidget.clear()`` removes the items but leaves the widgets set with
    ``setItemWidget`` alive, so each rebuild would leak the previous rows.
    """
    for i in range(list_widget.count()):
        row = list_widget.itemWidget(list_widget.item(i))
        if row is not None:
            row.deleteLater()
    list_widget.clear()
