"""Reusable widgets: the neon toggle, section label, and connection dot."""

from PySide6.QtCore import (Qt, QPropertyAnimation, Property, QSize,
                            QEasingCurve, QRectF)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QAbstractButton, QLabel, QWidget

from . import theme


class NeonToggle(QAbstractButton):
    """An iOS-style switch with a neon-green active state and animated knob."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._track_w = 48
        self._track_h = 26
        self.setFixedSize(self._track_w, self._track_h)
        self._offset = 3.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self):
        return QSize(self._track_w, self._track_h)

    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(float, get_offset, set_offset)

    def _animate(self, checked):
        start = self._offset
        end = (self._track_w - self._track_h + 3) if checked else 3
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(float(end))
        self._anim.start()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self._track_h / 2
        enabled = self.isEnabled()

        if self.isChecked():
            track = QColor(theme.ACCENT_DIM)
            knob = QColor(theme.ACCENT)
            if not enabled:
                track = QColor(theme.BORDER)
                knob = QColor(theme.TEXT_FAINT)
        else:
            track = QColor(theme.BORDER)
            knob = QColor(theme.TEXT_DIM if enabled else theme.TEXT_FAINT)

        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, self._track_w, self._track_h, r, r)

        kd = self._track_h - 6
        p.setBrush(knob)
        p.drawEllipse(QRectF(self._offset, 3, kd, kd))
        p.end()


class SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self.setObjectName("sectionLabel")


class StatusDot(QWidget):
    """A small colored dot used for the connection indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor(theme.TEXT_FAINT)

    def set_color(self, color_hex):
        self._color = QColor(color_hex)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        glow = QColor(self._color)
        glow.setAlpha(60)
        p.setBrush(glow)
        p.drawEllipse(0, 0, 12, 12)
        p.setBrush(self._color)
        p.drawEllipse(3, 3, 6, 6)
        p.end()
