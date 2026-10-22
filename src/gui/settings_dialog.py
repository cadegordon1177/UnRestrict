"""Settings dialog: dry run, safety prefs, about / credits."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame)

from . import theme, icons
from .widgets import NeonToggle, SectionLabel

APP_VERSION = "1.0.0"


class _ToggleRow(QFrame):
    def __init__(self, title, desc, checked, on_change, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(14)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 14px; font-weight: 600;")
        d = QLabel(desc)
        d.setObjectName("hint")
        d.setWordWrap(True)
        col.addWidget(t)
        col.addWidget(d)
        lay.addLayout(col, 1)
        self.toggle = NeonToggle()
        self.toggle.setChecked(checked)
        self.toggle.toggled.connect(on_change)
        lay.addWidget(self.toggle, 0, Qt.AlignVCenter)


class SettingsDialog(QDialog):
    def __init__(self, state, dm, parent=None):
        super().__init__(parent)
        self.state = state
        self.dm = dm
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setStyleSheet(theme.stylesheet())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(14)

        header = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(icons.svg_pixmap("gear", theme.TEXT, 24))
        header.addWidget(ic, 0, Qt.AlignVCenter)
        h = QLabel("Settings")
        h.setObjectName("title")
        header.addWidget(h, 1)
        lay.addLayout(header)

        lay.addWidget(SectionLabel("Testing"))
        lay.addWidget(_ToggleRow(
            "Dry run",
            "Run all checks and build the payload, but do not send anything to "
            "the device. Every step is logged.",
            self.state.dry_run, self._set_dry_run))

        lay.addWidget(SectionLabel("Safety"))
        lay.addWidget(_ToggleRow(
            "Reboot automatically after applying",
            "Let the device restart on its own once changes are written.",
            self.dm.pref_manager.auto_reboot, self._set_auto_reboot))

        lay.addWidget(SectionLabel("About"))
        about = QFrame()
        about.setObjectName("card")
        al = QVBoxLayout(about)
        al.setContentsMargins(16, 14, 16, 14)
        al.setSpacing(6)
        name = QLabel(f"UnRestrict  v{APP_VERSION}")
        name.setStyleSheet("font-size: 15px; font-weight: 700;")
        al.addWidget(name)
        lic = QLabel("Licensed under the GNU AGPL v3.0.")
        lic.setObjectName("hint")
        al.addWidget(lic)
        lay.addWidget(about)

        btns = QHBoxLayout()
        btns.addStretch(1)
        close = QPushButton("Close")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        btns.addWidget(close)
        lay.addLayout(btns)

    def _set_dry_run(self, value):
        self.state.dry_run = value

    def _set_auto_reboot(self, value):
        self.dm.pref_manager.auto_reboot = value
