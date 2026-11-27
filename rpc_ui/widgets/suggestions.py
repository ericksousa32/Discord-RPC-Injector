"""Suggestion list anchored to a text field (QCompleter with rich rows).

Clicking or focusing the field shows the full list; typing filters it.
Choosing an item emits ``picked(key)``. QCompleter handles focus
and the keyboard (↑/↓, Enter, Esc) without taking the cursor from the field.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QModelIndex, QObject, QRect, QSize, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QCompleter, QLineEdit, QStyle, QStyledItemDelegate

TITLE_ROLE = Qt.DisplayRole
SUBTITLE_ROLE = Qt.UserRole + 1
KEY_ROLE = Qt.UserRole + 2
SEARCH_ROLE = Qt.UserRole + 3
VALUE_ROLE = Qt.UserRole + 4     # text placed in the field when chosen
TRAILING_ROLE = Qt.UserRole + 5  # short text to the right of the title


@dataclass
class Suggestion:
    key: str
    title: str
    subtitle: str = ""
    value: str = ""
    search: str = ""
    trailing: str = ""


class _Filter(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tokens: list[str] = []

    def set_query(self, text: str) -> None:
        if hasattr(self, "beginFilterChange"):
            self.beginFilterChange()
            self._tokens = text.casefold().split()
            self.endFilterChange()
        else:  # Qt < 6.10
            self._tokens = text.casefold().split()
            self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        if not self._tokens:
            return True
        hay = self.sourceModel().index(row, 0, parent).data(SEARCH_ROLE) or ""
        return all(t in hay for t in self._tokens)


class _RowDelegate(QStyledItemDelegate):
    """Two lines: bold title and faded subtitle."""

    PAD_X, PAD_Y = 12, 8

    def sizeHint(self, option, index):
        fm = option.fontMetrics
        return QSize(200, fm.height() * 2 + self.PAD_Y * 2 + 4)

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        pal = option.palette
        r = option.rect.adjusted(4, 2, -4, -2)
        if option.state & (QStyle.State_Selected | QStyle.State_MouseOver):
            hl = QColor(pal.color(QPalette.Highlight))
            hl.setAlpha(70 if option.state & QStyle.State_Selected else 40)
            painter.setBrush(hl)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, 6, 6)

        text_rect = r.adjusted(self.PAD_X, self.PAD_Y - 2, -self.PAD_X, -self.PAD_Y + 2)
        fm = option.fontMetrics
        title_font = QFont(option.font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(pal.color(QPalette.Text))
        top = QRect(text_rect.left(), text_rect.top(), text_rect.width(), fm.height() + 2)
        trailing = index.data(TRAILING_ROLE) or ""
        trailing_w = fm.horizontalAdvance(trailing) + 16 if trailing else 0
        title_rect = top.adjusted(0, 0, -trailing_w, 0)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(title_font).elidedText(index.data(TITLE_ROLE) or "",
                                                             Qt.ElideRight, title_rect.width()))
        if trailing:
            painter.setFont(option.font)
            painter.setPen(pal.color(QPalette.PlaceholderText))
            painter.drawText(top, Qt.AlignRight | Qt.AlignVCenter, trailing)

        sub = index.data(SUBTITLE_ROLE) or ""
        if sub:
            painter.setFont(option.font)
            painter.setPen(pal.color(QPalette.PlaceholderText))
            bottom = QRect(text_rect.left(), top.bottom() + 2, text_rect.width(), fm.height() + 2)
            painter.drawText(bottom, Qt.AlignLeft | Qt.AlignVCenter,
                             fm.elidedText(sub, Qt.ElideRight, bottom.width()))
        painter.restore()


class _NoAutoSelectCompleter(QCompleter):
    """Does not highlight on its own the item whose value starts with the typed text.

    So Enter only picks an item when the user selected it (arrows or
    mouse); otherwise Enter stays with the field.
    """

    def splitPath(self, path):
        return ["\0"]  # never matches an item


class SuggestionList(QObject):
    picked = Signal(str)

    MAX_VISIBLE = 6

    def __init__(self, field: QLineEdit):
        super().__init__(field)
        self.field = field
        self._model = QStandardItemModel(self)
        self._proxy = _Filter(self)
        self._proxy.setSourceModel(self._model)

        self.completer = _NoAutoSelectCompleter(self._proxy, self)
        # The filter is ours (multi-word); QCompleter only shows the list.
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCompletionRole(VALUE_ROLE)
        self.completer.setMaxVisibleItems(self.MAX_VISIBLE)
        popup = self.completer.popup()
        popup.setObjectName("SuggestionPopup")
        popup.setItemDelegate(_RowDelegate(popup))
        popup.setMouseTracking(True)
        popup.setUniformItemSizes(True)
        field.setCompleter(self.completer)

        self.completer.activated[QModelIndex].connect(self._on_activated)
        field.textEdited.connect(self._on_edited)
        field.installEventFilter(self)

    # ── data ────────────────────────────────────────────────────────────────
    def set_suggestions(self, items: list[Suggestion]) -> None:
        self._model.clear()
        for s in items:
            it = QStandardItem(s.title)
            it.setData(s.subtitle, SUBTITLE_ROLE)
            it.setData(s.key, KEY_ROLE)
            it.setData(s.value, VALUE_ROLE)
            it.setData(s.trailing, TRAILING_ROLE)
            it.setData(" ".join((s.title, s.subtitle, s.value, s.search)).casefold(), SEARCH_ROLE)
            it.setEditable(False)
            self._model.appendRow(it)
        if not items:
            self.hide()

    def count(self) -> int:
        return self._model.rowCount()

    def visible_keys(self) -> list[str]:
        return [self._proxy.index(r, 0).data(KEY_ROLE) for r in range(self._proxy.rowCount())]

    # ── display ─────────────────────────────────────────────────────────────
    def is_open(self) -> bool:
        return self.completer.popup().isVisible()

    def open(self, query: str = "") -> bool:
        if not self.field.isEnabled() or self.count() == 0:
            return False
        self._proxy.set_query(query)
        if self._proxy.rowCount() == 0:
            self.hide()
            return False
        rect = self.field.rect()
        rect.setWidth(self.field.width())
        self.completer.complete(rect)
        popup = self.completer.popup()
        popup.setCurrentIndex(self._proxy.index(-1, 0))
        rows = min(self._proxy.rowCount(), self.MAX_VISIBLE)
        frame = popup.frameWidth() * 2 + 2
        popup.setFixedHeight(popup.sizeHintForRow(0) * rows + frame)
        return True

    def hide(self) -> None:
        self.completer.popup().hide()

    def choose_row(self, row: int) -> None:
        """Chooses the visible row ``row`` (used by shortcuts and tests)."""
        self._on_activated(self._proxy.index(row, 0))
        self.hide()

    # ── events ──────────────────────────────────────────────────────────────
    def _on_edited(self, text: str) -> None:
        self.open(text)

    def _on_activated(self, index) -> None:
        key = index.data(KEY_ROLE)
        if key is not None:
            self.picked.emit(key)

    def owns_return(self) -> bool:
        """True when the current Enter is going to choose an item from the list.

        QCompleter forwards Enter to the field (``returnPressed``) *before*
        emitting ``activated``; whoever handles ``returnPressed`` checks this to
        avoid acting twice.
        """
        return self.is_open() and self.completer.popup().currentIndex().isValid()

    def eventFilter(self, obj, event):
        if obj is self.field:
            et = event.type()
            if et == QEvent.MouseButtonPress and not self.is_open():
                self.open()
            elif et == QEvent.KeyPress and event.key() == Qt.Key_Down and not self.is_open():
                self.open()
                return True
        return False

