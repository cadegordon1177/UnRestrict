"""Screen 1: CONNECT - auto-detects the iPhone and shows connection state."""

from PySide6.QtCore import (Qt, QByteArray, QPropertyAnimation, QEasingCurve,
                            QTimer, Signal)
from PySide6.QtGui import QPainter, QColor, QRadialGradient
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGraphicsOpacityEffect)
from PySide6.QtSvgWidgets import QSvgWidget

from .. import theme, icons
from ..app_state import ConnState
from ..widgets import StatusDot


class ConnectScreen(QWidget):
    proceed = Signal()  # ask main window to advance to Configure

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setObjectName("screen")
        self.state = state
        self._advance_timer = QTimer(self)
        self._advance_timer.setSingleShot(True)
        self._advance_timer.timeout.connect(self.proceed.emit)

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 36, 48, 36)
        root.addStretch(1)

        # phone glyph
        self.phone = QSvgWidget()
        self.phone.setFixedSize(150, 266)  # matches the 140:248 viewbox aspect
        self._set_phone(theme.TEXT_DIM, "dots")
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.phone)
        row.addStretch(1)
        root.addLayout(row)

        # gentle breathing pulse
        self._opacity = QGraphicsOpacityEffect(self.phone)
        self._opacity.setOpacity(1.0)
        self.phone.setGraphicsEffect(self._opacity)
        self._pulse = QPropertyAnimation(self._opacity, b"opacity", self)
        self._pulse.setDuration(1600)
        self._pulse.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_dir = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start(1600)
        self._tick_pulse()

        root.addSpacing(26)

        self.title = QLabel("Plug in your iPhone")
        self.title.setObjectName("display")
        self.title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title, 0, Qt.AlignCenter)

        root.addSpacing(12)
        status_row = QHBoxLayout()
        status_row.setSpacing(9)
        status_row.addStretch(1)
        self.dot = StatusDot()
        status_row.addWidget(self.dot, 0, Qt.AlignVCenter)
        self.status = QLabel("Waiting for a device")
        self.status.setObjectName("subtitle")
        status_row.addWidget(self.status, 0, Qt.AlignVCenter)
        status_row.addStretch(1)
        root.addLayout(status_row)

        root.addSpacing(8)
        self.detail = QLabel("")
        self.detail.setObjectName("hint")
        self.detail.setAlignment(Qt.AlignCenter)
        self.detail.setWordWrap(True)
        self.detail.setFixedWidth(440)
        drow = QHBoxLayout()
        drow.addStretch(1)
        drow.addWidget(self.detail)
        drow.addStretch(1)
        root.addLayout(drow)

        root.addSpacing(26)
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setObjectName("primary")
        self.continue_btn.setStyleSheet(
            "padding: 11px 30px; font-size: 14px; letter-spacing: 1px;")
        self.continue_btn.setFixedWidth(190)
        self.continue_btn.setCursor(Qt.PointingHandCursor)
        self.continue_btn.clicked.connect(self.proceed.emit)
        self.continue_btn.hide()
        root.addWidget(self.continue_btn, 0, Qt.AlignCenter)

        root.addStretch(1)

    def _tick_pulse(self):
        self._pulse_dir = not self._pulse_dir
        self._pulse.stop()
        if self._pulse_dir:
            self._pulse.setStartValue(0.55)
            self._pulse.setEndValue(1.0)
        else:
            self._pulse.setStartValue(1.0)
            self._pulse.setEndValue(0.55)
        self._pulse.start()

    def _set_phone(self, color_hex, glyph):
        self.phone.load(QByteArray(icons.phone_markup(color_hex, glyph)))

    # ---- state rendering ----
    def render_state(self, state: ConnState, info: dict, error: str):
        self._advance_timer.stop()
        self.continue_btn.hide()

        if state == ConnState.WAITING:
            self._set_phone(theme.TEXT_DIM, "dots")
            self.dot.set_color(theme.TEXT_FAINT)
            self.title.setText("Plug in your iPhone")
            self.status.setText("Waiting for a device")
            self.detail.setText("Connect your iPhone with a cable to get started.")
        elif state == ConnState.LOCKED:
            self._set_phone(theme.AMBER, "lock")
            self.dot.set_color(theme.AMBER)
            self.title.setText("Unlock your iPhone")
            self.status.setText("Locked or not trusted")
            self.detail.setText('Unlock your iPhone and tap "Trust", then enter your passcode.')
        elif state == ConnState.UNSUPPORTED:
            self._set_phone(theme.RED, "cross")
            self.dot.set_color(theme.RED)
            self.title.setText("Unsupported iOS version")
            name = (info or {}).get("name", "Device")
            ver = (info or {}).get("version", "?")
            self.status.setText(f"{name} · iOS {ver}")
            self.detail.setText(error or "This iOS version is not supported.")
        elif state == ConnState.ERROR:
            self._set_phone(theme.RED, "cross")
            self.dot.set_color(theme.RED)
            self.title.setText("Connection error")
            self.status.setText("Something went wrong")
            self.detail.setText(error or "Unknown error.")
        elif state == ConnState.CONNECTED:
            self._set_phone(theme.ACCENT, "check")
            self.dot.set_color(theme.ACCENT)
            self.title.setText("Connected")
            name = (info or {}).get("name", "iPhone")
            model = (info or {}).get("model", "")
            ver = (info or {}).get("version", "")
            self.status.setText(name)
            self.detail.setText(f"{model}  ·  iOS {ver}")
            self.continue_btn.show()
            self._advance_timer.start(1100)

    def paintEvent(self, _event):
        # soft radial glow from the upper center - techy, not a hacker grid
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(theme.BG))
        grad = QRadialGradient(self.width() * 0.5, self.height() * 0.32,
                               self.width() * 0.7)
        grad.setColorAt(0.0, QColor(theme.BG_TOP))
        grad.setColorAt(1.0, QColor(theme.BG))
        p.fillRect(self.rect(), grad)
        p.end()
