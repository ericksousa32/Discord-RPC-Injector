"""Notificações passivas sobrepostas à janela (estilo Kirigami passiveNotification)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..i18n import tr
from .buttons import Button
from .style import set_prop


class Toast(QFrame):
    closed = Signal()

    def __init__(self, title: str, text: str = "", tone: str = "info", action: str | None = None,
                 on_action=None, timeout_ms: int = 4000, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        set_prop(self, "tone", tone)
        self.tone = tone
        self._closed = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 8, 10)
        lay.setSpacing(10)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        self.title_label = QLabel(title, objectName="ToastTitle")
        texts.addWidget(self.title_label)
        self.text_label = QLabel(text, objectName="ToastText")
        self.text_label.setWordWrap(True)
        self.text_label.setVisible(bool(text))
        texts.addWidget(self.text_label)
        lay.addLayout(texts, 1)
        self.action_button = None
        if action:
            self.action_button = Button(action, variant="flat")
            self.action_button.clicked.connect(lambda: (on_action and on_action(), self.dismiss()))
            lay.addWidget(self.action_button)
        close = Button("", "window-close", "flat", tooltip=tr("common.close"))
        close.setFixedSize(28, 28)
        close.clicked.connect(self.dismiss)
        lay.addWidget(close)
        self.setMaximumWidth(460)

        self.timer = QTimer(self, singleShot=True)
        self.timer.timeout.connect(self.dismiss)
        self._remaining = 0
        if timeout_ms > 0:
            self.timer.start(timeout_ms)

    def enterEvent(self, e):  # pausa o tempo enquanto o mouse está em cima
        if self.timer.isActive():
            self._remaining = self.timer.remainingTime()
            self.timer.stop()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self._remaining > 0:
            self.timer.start(max(self._remaining, 1200))
            self._remaining = 0
        super().leaveEvent(e)

    def dismiss(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.timer.stop()
        self.hide()
        self.closed.emit()
        self.deleteLater()


class ToastHost(QObject):
    """Empilha toasts no canto inferior direito do widget ``target``."""

    MAX = 3

    def __init__(self, target: QWidget):
        super().__init__(target)
        self._target = target
        self.toasts: list[Toast] = []
        target.installEventFilter(self)

    def show(self, title: str, text: str = "", tone: str = "info", action: str | None = None,
             on_action=None, timeout_ms: int = 4000) -> Toast:
        toast = Toast(title, text, tone, action, on_action, timeout_ms, self._target)
        toast.closed.connect(lambda t=toast: self._remove(t))
        self.toasts.append(toast)
        while len(self.toasts) > self.MAX:
            self.toasts[0].dismiss()
        toast.show()
        toast.raise_()
        self._layout()
        return toast

    def _remove(self, toast: Toast) -> None:
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._layout()

    def _layout(self) -> None:
        w, y = self._target.width(), self._target.height() - 20
        for toast in reversed(self.toasts):
            width = min(max(toast.sizeHint().width(), 320), 460)
            toast.resize(width, toast.heightForWidth(width) if toast.hasHeightForWidth()
                         else toast.sizeHint().height())
            y -= toast.height()
            toast.move(QPoint(w - width - 24, y))
            y -= 8

    def eventFilter(self, obj, event):
        if obj is self._target and event.type() == QEvent.Resize:
            self._layout()
        return False
