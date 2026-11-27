from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

from .icons import icon as theme_icon


class NavItem(QPushButton):
    def __init__(self, key: str, text: str, icon: str, parent=None):
        super().__init__(text, parent)
        self.key = key
        self.setObjectName("NavItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(theme_icon(icon))
        self.setIconSize(QSize(18, 18))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 10, 0)
        lay.addStretch(1)
        self.badge = QLabel(objectName="NavBadge")
        self.badge.hide()
        lay.addWidget(self.badge)

    def set_badge(self, value) -> None:
        self.badge.setText(str(value))
        self.badge.setVisible(bool(value))


class Sidebar(QFrame):
    """Side navigation (Kirigami GlobalDrawer style) with a free footer."""

    current_changed = Signal(str)

    def __init__(self, title: str, subtitle: str = "", logo: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(232)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 14)
        lay.setSpacing(4)

        brand = QHBoxLayout()
        brand.setContentsMargins(6, 0, 0, 12)
        brand.setSpacing(10)
        if logo:
            pm = QPixmap(logo)
            if not pm.isNull():
                lg = QLabel()
                lg.setPixmap(pm.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                brand.addWidget(lg)
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(QLabel(title, objectName="SidebarTitle"))
        self.subtitle_label = QLabel(subtitle, objectName="SidebarSubtitle")
        self.subtitle_label.setVisible(bool(subtitle))
        names.addWidget(self.subtitle_label)
        brand.addLayout(names, 1)
        lay.addLayout(brand)

        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(2)
        lay.addLayout(self._items_layout)
        lay.addStretch(1)
        self.footer = QVBoxLayout()
        self.footer.setSpacing(8)
        lay.addLayout(self.footer)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self.items: dict[str, NavItem] = {}

    def add_section(self, text: str) -> QLabel:
        lbl = QLabel(text.upper(), objectName="SidebarSection")
        lbl.setContentsMargins(12, 12, 0, 4)
        self._items_layout.addWidget(lbl)
        return lbl

    def add_item(self, key: str, text: str, icon: str, shortcut: str | None = None) -> NavItem:
        item = NavItem(key, text, icon)
        item.shortcut_text = shortcut
        if shortcut:
            item.setShortcut(shortcut)
        self.set_item_text(key, text, item)
        item.clicked.connect(lambda: self.current_changed.emit(key))
        self._group.addButton(item)
        self._items_layout.addWidget(item)
        self.items[key] = item
        return item

    def set_item_text(self, key: str, text: str, item: NavItem | None = None) -> None:
        """Set a nav item's label; its tooltip repeats the label with the shortcut."""
        item = item or self.items[key]
        item.setText(text)
        shortcut = getattr(item, "shortcut_text", None)
        item.setToolTip(f"{text} ({shortcut})" if shortcut else "")

    def set_current(self, key: str) -> None:
        if key in self.items:
            self.items[key].setChecked(True)

    def current(self) -> str | None:
        btn = self._group.checkedButton()
        return btn.key if btn else None
