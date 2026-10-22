"""Modal confirmation sheet used before an apply or a restore."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame)

from . import theme, icons


class ConfirmDialog(QDialog):
    def __init__(self, header, lines, warning, confirm_label,
                 icon_name="bolt", warn_level="amber", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm")
        self.setModal(True)
        self.setMinimumWidth(470)
        self.setStyleSheet(theme.stylesheet())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(14)

        row = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(icons.svg_pixmap(icon_name, theme.ACCENT, 26))
        row.addWidget(ic, 0, Qt.AlignVCenter)
        htext = QLabel(header)
        htext.setStyleSheet("font-size: 18px; font-weight: 700;")
        htext.setWordWrap(True)
        row.addWidget(htext, 1)
        lay.addLayout(row)

        if lines:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            cl.setSpacing(7)
            for t in lines:
                r = QHBoxLayout()
                r.setSpacing(10)
                dot = QLabel()
                dot.setPixmap(icons.svg_pixmap("check", theme.ACCENT, 15))
                r.addWidget(dot, 0, Qt.AlignTop)
                lbl = QLabel(t)
                lbl.setStyleSheet("font-size: 13px;")
                lbl.setWordWrap(True)
                r.addWidget(lbl, 1)
                cl.addLayout(r)
            lay.addWidget(card)

        if warning:
            color = {"amber": theme.AMBER, "red": theme.RED,
                     "dim": theme.TEXT_DIM}.get(warn_level, theme.AMBER)
            w = QLabel(warning)
            w.setWordWrap(True)
            w.setStyleSheet(f"color:{color}; font-size:12px;")
            lay.addWidget(w)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        go = QPushButton(confirm_label)
        go.setObjectName("primary")
        go.setStyleSheet("padding: 11px 24px; font-size: 14px; letter-spacing: 1px;")
        go.setCursor(Qt.PointingHandCursor)
        go.clicked.connect(self.accept)
        btns.addWidget(go)
        lay.addLayout(btns)
