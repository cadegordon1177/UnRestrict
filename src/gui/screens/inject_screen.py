"""Screen 3: INJECT - progress, a real log console, and the run result."""

import re
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QPlainTextEdit, QProgressBar,
                               QCheckBox, QFileDialog, QLineEdit)

from .. import theme, icons
from ..log_bus import log_bus, LogLine
from ..app_state import InjectState

_LEVEL_WIDTH = 5  # widest tag is ERROR; fixed-width keeps columns aligned


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class InjectScreen(QWidget):
    back_requested = Signal()
    retry_requested = Signal()
    export_requested = Signal(str)  # emits the full log text for diagnostics

    _PCT = re.compile(r"\(\s*([0-9]+(?:\.[0-9]+)?)%")

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setObjectName("screen")
        self.state = state
        self._pin = True
        self._programmatic_scroll = False
        self._lines: list[LogLine] = []
        self._filter = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.sp(5), theme.sp(5), theme.sp(5), theme.sp(5))
        root.setSpacing(theme.sp(3))

        banner = QHBoxLayout()
        banner.setSpacing(theme.sp(2))
        self.status_icon = QLabel()
        self.status_icon.setPixmap(icons.svg_pixmap("terminal", theme.ACCENT, 22))
        banner.addWidget(self.status_icon, 0, Qt.AlignVCenter)
        self.status_label = QLabel("Injecting")
        self.status_label.setObjectName("display")
        self.status_label.setStyleSheet(f"font-size:21px; font-weight:700;")
        banner.addWidget(self.status_label, 0, Qt.AlignVCenter)
        banner.addStretch(1)
        root.addLayout(banner)

        self.detail = QLabel("")
        self.detail.setObjectName("subtitle")
        self.detail.setWordWrap(True)
        root.addWidget(self.detail)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        search_row = QHBoxLayout()
        search_row.setSpacing(theme.sp(2))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find in log")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_search)
        self.search.addAction(icons.svg_icon("search", theme.TEXT_FAINT, 15),
                              QLineEdit.LeadingPosition)
        search_row.addWidget(self.search)
        root.addLayout(search_row)

        self.log = QPlainTextEdit()
        self.log.setObjectName("logBox")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.verticalScrollBar().valueChanged.connect(self._on_scroll)
        root.addWidget(self.log, 1)

        controls = QHBoxLayout()
        controls.setSpacing(theme.sp(2))
        self.pin_check = QCheckBox("Pin to bottom")
        self.pin_check.setChecked(True)
        self.pin_check.toggled.connect(self._on_pin_toggle)
        controls.addWidget(self.pin_check)
        controls.addStretch(1)
        self.copy_btn = self._tool_btn("copy", "Copy", self._copy_log)
        self.save_btn = self._tool_btn("save", "Save", self._save_log)
        self.export_btn = self._tool_btn("shield", "Export diagnostics",
                                         self._export_diag)
        self.clear_btn = self._tool_btn("cross", "Clear", self._clear_log)
        for b in (self.copy_btn, self.save_btn, self.export_btn, self.clear_btn):
            controls.addWidget(b)
        root.addLayout(controls)

        result = QHBoxLayout()
        self.back_btn = QPushButton("  Back")
        self.back_btn.setObjectName("ghost")
        self.back_btn.setIcon(icons.svg_icon("back", theme.TEXT, 18))
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_requested.emit)
        result.addWidget(self.back_btn)
        result.addStretch(1)
        self.retry_btn = QPushButton("Retry")
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.clicked.connect(self.retry_requested.emit)
        result.addWidget(self.retry_btn)
        root.addLayout(result)

        log_bus.line.connect(self._append_line)

    def _tool_btn(self, icon_name, text, slot):
        btn = QPushButton("  " + text)
        btn.setObjectName("ghost")
        btn.setIcon(icons.svg_icon(icon_name, theme.TEXT_DIM, 15))
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    # ---- log rendering ----
    def _row_html(self, line: LogLine) -> str:
        color = theme.LEVEL_COLORS.get(line.level, theme.TEXT)
        tag = line.level.ljust(_LEVEL_WIDTH)
        text = f"{line.ts}  {tag}  {line.msg}"
        return (f'<span style="color:{color}; white-space:pre;">'
                f'{_html_escape(text)}</span>')

    def _append_line(self, line: LogLine):
        self._lines.append(line)
        if self._filter and self._filter not in line.msg.lower():
            pass
        else:
            self.log.appendHtml(self._row_html(line))
            if self._pin:
                self._scroll_to_bottom()
        m = self._PCT.search(line.msg)
        if m:
            try:
                self.progress.setValue(int(float(m.group(1))))
            except ValueError:
                pass

    def _rerender(self):
        self.log.clear()
        for line in self._lines:
            if not self._filter or self._filter in line.msg.lower():
                self.log.appendHtml(self._row_html(line))
        if self._pin:
            self._scroll_to_bottom()

    def _on_search(self, text):
        self._filter = text.strip().lower()
        self._rerender()

    def _scroll_to_bottom(self):
        self._programmatic_scroll = True
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())
        self.log.moveCursor(QTextCursor.End)
        self._programmatic_scroll = False

    def _on_scroll(self, _value):
        if self._programmatic_scroll:
            return
        bar = self.log.verticalScrollBar()
        if bar.value() < bar.maximum() - 2 and self._pin:
            self._pin = False
            self.pin_check.setChecked(False)

    def _on_pin_toggle(self, value):
        self._pin = value
        if value:
            self._scroll_to_bottom()

    def full_text(self) -> str:
        return "\n".join(line.formatted() for line in self._lines)

    def _copy_log(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.full_text())

    def _save_log(self):
        default = time.strftime("unrestrict-log-%Y%m%d-%H%M%S.txt")
        path, _ = QFileDialog.getSaveFileName(self, "Save log", default,
                                              "Text files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.full_text())

    def _export_diag(self):
        self.export_requested.emit(self.full_text())

    def _clear_log(self):
        if self.state.inject_state != InjectState.RUNNING:
            self._lines.clear()
            self.log.clear()
            self.progress.setValue(0)

    # ---- run lifecycle ----
    def begin(self, dry_run: bool, mode: str = "apply"):
        self._lines.clear()
        self.log.clear()
        self.search.clear()
        self.progress.setValue(0)
        self._pin = True
        self.pin_check.setChecked(True)
        self.status_icon.setPixmap(icons.svg_pixmap("terminal", theme.ACCENT, 22))
        self.status_label.setStyleSheet(
            f"font-size:21px; font-weight:700; color:{theme.TEXT};")
        if dry_run:
            self.status_label.setText("Dry run")
        elif mode == "restore":
            self.status_label.setText("Restoring")
        else:
            self.status_label.setText("Injecting")
        self.detail.setText("Keep your iPhone connected. Do not unplug it.")
        self._set_controls(running=True)

    def finish(self, success: bool, message: str, detail: str):
        self._set_controls(running=False, success=success)
        if success:
            self.progress.setValue(100)
            self.status_icon.setPixmap(icons.svg_pixmap("check", theme.ACCENT, 22))
            self.status_label.setText("Done")
            self.status_label.setStyleSheet(
                f"font-size:21px; font-weight:700; color:{theme.ACCENT};")
        else:
            self.status_icon.setPixmap(icons.svg_pixmap("warning", theme.RED, 22))
            self.status_label.setText("Failed")
            self.status_label.setStyleSheet(
                f"font-size:21px; font-weight:700; color:{theme.RED};")
        self.detail.setText(message + (("  " + detail) if detail else ""))

    def _set_controls(self, running: bool, success: bool = False):
        self.clear_btn.setEnabled(not running)
        self.back_btn.setVisible(not running)
        self.retry_btn.setVisible(not running and not success)
