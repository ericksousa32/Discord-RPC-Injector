"""Preview of how the activity appears on the Discord profile."""

from __future__ import annotations

import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr


class ActivityPreview(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)
        self.heading = QLabel(tr("preview.playing"), objectName="PreviewHeading")
        lay.addWidget(self.heading)

        row = QHBoxLayout()
        row.setSpacing(12)
        art = QWidget()
        art.setFixedSize(76, 76)
        self.large = QLabel("RPC", art, objectName="PreviewImage", alignment=Qt.AlignCenter)
        self.large.setGeometry(0, 0, 70, 70)
        self.small = QLabel(art, objectName="PreviewSmallImage")
        self.small.setGeometry(52, 52, 22, 22)
        row.addWidget(art, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.app = QLabel(objectName="PreviewApp")
        self.details = QLabel(objectName="PreviewLine")
        self.state = QLabel(objectName="PreviewLine")
        self.elapsed = QLabel(objectName="PreviewLine")
        for w in (self.app, self.details, self.state, self.elapsed):
            w.setTextInteractionFlags(Qt.NoTextInteraction)
            info.addWidget(w)
        info.addStretch(1)
        row.addLayout(info, 1)
        lay.addLayout(row)

        self.btn1 = QPushButton(objectName="PreviewButton")
        self.btn2 = QPushButton(objectName="PreviewButton")
        for b in (self.btn1, self.btn2):
            b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.ArrowCursor)
            lay.addWidget(b)

        self._start_ts: int | None = None
        self._show_elapsed = False
        self._timer = QTimer(self, interval=1000)
        self._timer.timeout.connect(self._tick)

    def retranslate(self) -> None:
        self.heading.setText(tr("preview.playing"))

    def update_from(self, presence, start_ts: int | None = None, app_name: str = "") -> None:
        if not app_name:
            app_name = tr("preview.app", app_id=presence.app_id) if presence.app_id else tr("preview.your_app")
        self.app.setText(app_name)
        self.details.setText(presence.details or "")
        self.details.setVisible(bool(presence.details))
        party = ""
        if presence.party_size.strip() and presence.party_max.strip():
            party = " " + tr("preview.party", size=presence.party_size, max=presence.party_max)
        self.state.setText((presence.state or "") + party)
        self.state.setVisible(bool(presence.state or party))
        self.large.setText((presence.large_key or "RPC")[:3].upper())
        self.large.setToolTip(presence.large_text)
        self.small.setVisible(bool(presence.small_key))
        self.small.setToolTip(presence.small_text)
        for btn, label, url in ((self.btn1, presence.btn1_label, presence.btn1_url),
                                (self.btn2, presence.btn2_label, presence.btn2_url)):
            btn.setText(label)
            btn.setToolTip(url)
            btn.setVisible(bool(label.strip() and url.strip()))
        self._show_elapsed = presence.show_elapsed
        self._start_ts = start_ts
        self._tick()
        if presence.show_elapsed:
            self._timer.start()
        else:
            self._timer.stop()

    def _tick(self) -> None:
        if not self._show_elapsed:
            self.elapsed.hide()
            return
        secs = max(0, int(time.time()) - self._start_ts) if self._start_ts else 0
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        text = f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"
        self.elapsed.setText(tr("preview.elapsed", time=text))
        self.elapsed.show()
