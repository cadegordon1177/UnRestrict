"""Screen 2: CONFIGURE - live preflight, options, and the inject/restore actions."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea, QSizePolicy)

from .. import theme, icons
from ..app_state import ConnState, HERO_OPTION, EXTRA_OPTIONS
from ..widgets import NeonToggle, SectionLabel, StatusDot
from src.devicemanagement.preflight import Status

_STATUS_KEY = {
    Status.PASS: "pass", Status.WARN: "warn",
    Status.FAIL: "fail", Status.CHECKING: "checking",
}


class CheckRow(QWidget):
    """One preflight row: status icon, label, detail, and an inline fix."""

    def __init__(self, check, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, theme.sp(1), 0, theme.sp(1))
        lay.setSpacing(2)

        top = QHBoxLayout()
        top.setSpacing(theme.sp(2))
        color, icon_name = theme.STATUS_STYLE[_STATUS_KEY[check.status]]
        dot = QLabel()
        dot.setPixmap(icons.svg_pixmap(icon_name, color, 16))
        dot.setFixedWidth(18)
        top.addWidget(dot, 0, Qt.AlignVCenter)

        label = QLabel(check.label)
        label.setStyleSheet(f"font-size:{theme.FS_BODY}px; color:{theme.TEXT};")
        top.addWidget(label, 0, Qt.AlignVCenter)
        top.addStretch(1)
        if check.detail:
            det = QLabel(check.detail)
            det.setObjectName("metaMono")
            top.addWidget(det, 0, Qt.AlignVCenter)
        lay.addLayout(top)

        if check.status != Status.PASS and check.fix:
            fix = QLabel(check.fix)
            fix.setWordWrap(True)
            fix.setStyleSheet(
                f"font-size:{theme.FS_SMALL}px; color:{color}; margin-left:26px;")
            lay.addWidget(fix)


class ExtraRow(QFrame):
    """A quiet, dense toggle row for an extra option."""

    toggled = Signal(str, bool)

    def __init__(self, option, parent=None):
        super().__init__(parent)
        self.setObjectName("extraRow")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(theme.sp(3), theme.sp(2), theme.sp(3), theme.sp(2))
        lay.setSpacing(theme.sp(3))

        col = QVBoxLayout()
        col.setSpacing(1)
        title = QLabel(option.title)
        title.setStyleSheet(f"font-size:{theme.FS_BODY}px; color:{theme.TEXT};")
        desc = QLabel(option.desc)
        desc.setObjectName("hint")
        desc.setWordWrap(True)
        col.addWidget(title)
        col.addWidget(desc)
        lay.addLayout(col, 1)

        self.toggle = NeonToggle()
        self.toggle.setChecked(option.default_on)
        self.toggle.toggled.connect(lambda v: self.toggled.emit(option.id, v))
        lay.addWidget(self.toggle, 0, Qt.AlignVCenter)


class ConfigureScreen(QWidget):
    inject_requested = Signal()
    restore_requested = Signal()
    settings_requested = Signal()

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setObjectName("screen")
        self.state = state

        root = QVBoxLayout(self)
        root.setContentsMargins(theme.sp(5), theme.sp(5), theme.sp(5), theme.sp(5))
        root.setSpacing(theme.sp(4))

        root.addWidget(self._build_top_bar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("screen")
        self.content = QVBoxLayout(inner)
        self.content.setContentsMargins(0, 0, theme.sp(2), 0)
        self.content.setSpacing(theme.sp(4))
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        self._build_preflight()
        self._build_hero()
        self._build_extras()
        self.content.addStretch(1)

        self.inject_btn = QPushButton("Inject")
        self.inject_btn.setObjectName("primary")
        self.inject_btn.setMinimumHeight(48)
        self.inject_btn.setCursor(Qt.PointingHandCursor)
        self.inject_btn.clicked.connect(self.inject_requested.emit)

        self.restore_btn = QPushButton("  Restore defaults")
        self.restore_btn.setObjectName("ghost")
        self.restore_btn.setMinimumHeight(48)
        self.restore_btn.setIcon(icons.svg_icon("back", theme.TEXT_DIM, 16))
        self.restore_btn.setCursor(Qt.PointingHandCursor)
        self.restore_btn.clicked.connect(self.restore_requested.emit)

        actions = QHBoxLayout()
        actions.setSpacing(theme.sp(3))
        actions.addWidget(self.restore_btn, 1)
        actions.addWidget(self.inject_btn, 2)
        root.addLayout(actions)

        self.state.options_changed.connect(self._update_actions)

    def _build_top_bar(self):
        bar = QFrame()
        bar.setObjectName("topBar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(theme.sp(4), theme.sp(3), theme.sp(3), theme.sp(3))
        lay.setSpacing(theme.sp(3))

        self.dev_name = QLabel("No device")
        self.dev_name.setStyleSheet(
            f"font-size:{theme.FS_TITLE}px; font-weight:{theme.W_MED};")
        self.dev_meta = QLabel("")
        self.dev_meta.setObjectName("metaMono")
        lay.addWidget(self.dev_name)
        lay.addWidget(self.dev_meta)
        lay.addStretch(1)

        self.dot = StatusDot()
        lay.addWidget(self.dot, 0, Qt.AlignVCenter)
        self.conn_text = QLabel("")
        self.conn_text.setObjectName("hint")
        lay.addWidget(self.conn_text)

        gear = QPushButton()
        gear.setObjectName("iconButton")
        gear.setIcon(icons.svg_icon("gear", theme.TEXT_DIM, 20))
        gear.setCursor(Qt.PointingHandCursor)
        gear.setToolTip("Settings")
        gear.clicked.connect(self.settings_requested.emit)
        lay.addWidget(gear)
        return bar

    def _build_preflight(self):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(theme.sp(4), theme.sp(3), theme.sp(4), theme.sp(3))
        lay.setSpacing(theme.sp(1))
        lay.addWidget(SectionLabel("Preflight"))
        self.preflight_rows = QVBoxLayout()
        self.preflight_rows.setSpacing(0)
        lay.addLayout(self.preflight_rows)
        self.content.addWidget(card)

    def _build_hero(self):
        card = QFrame()
        card.setObjectName("heroCard")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(theme.sp(5), theme.sp(5), theme.sp(5), theme.sp(5))
        lay.setSpacing(theme.sp(4))

        icon = QLabel()
        icon.setPixmap(icons.svg_pixmap("shield", theme.ACCENT, 32))
        lay.addWidget(icon, 0, Qt.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(theme.sp(2))
        t = QLabel(HERO_OPTION.title)
        t.setObjectName("display")
        t.setStyleSheet(f"font-size:21px; font-weight:700;")
        d = QLabel(HERO_OPTION.desc)
        d.setObjectName("subtitle")
        d.setWordWrap(True)
        col.addWidget(t)
        col.addWidget(d)
        lay.addLayout(col, 1)

        self.hero_toggle = NeonToggle()
        self.hero_toggle.setChecked(HERO_OPTION.default_on)
        self.hero_toggle.toggled.connect(
            lambda v: self.state.toggle(HERO_OPTION.id, v))
        lay.addWidget(self.hero_toggle, 0, Qt.AlignVCenter)
        self.content.addWidget(card)

    def _build_extras(self):
        wrap = QVBoxLayout()
        wrap.setSpacing(theme.sp(1))
        wrap.addWidget(SectionLabel("Extras"))
        groups = {}
        for opt in EXTRA_OPTIONS:
            groups.setdefault(opt.group, []).append(opt)
        for group in ("System", "Privacy"):
            if group not in groups:
                continue
            sub = QLabel(group.upper())
            sub.setStyleSheet(
                f"color:{theme.TEXT_FAINT}; font-size:10px; letter-spacing:1.5px; "
                f"margin-top:{theme.sp(2)}px;")
            wrap.addWidget(sub)
            for opt in groups[group]:
                row = ExtraRow(opt)
                row.toggled.connect(self.state.toggle)
                wrap.addWidget(row)
        holder = QWidget()
        holder.setObjectName("screen")
        holder.setLayout(wrap)
        self.content.addWidget(holder)

    # ---- refresh from state ----
    def refresh(self):
        info = self.state.device_info or {}
        self.dev_name.setText(info.get("name", "No device"))
        self.dev_meta.setText(
            f"iOS {info.get('version','')}   {info.get('model','')}" if info else "")

        connected = self.state.conn_state == ConnState.CONNECTED
        self.dot.set_color(theme.ACCENT if connected else theme.RED)
        self.conn_text.setText("Connected" if connected else "Disconnected")

        self._render_preflight()
        self._update_actions()

    def _render_preflight(self):
        while self.preflight_rows.count():
            item = self.preflight_rows.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        checks = self.state.preflight
        if not checks:
            placeholder = QLabel("Running checks…")
            placeholder.setObjectName("hint")
            placeholder.setContentsMargins(26, theme.sp(1), 0, theme.sp(1))
            self.preflight_rows.addWidget(placeholder)
            return
        for check in checks:
            self.preflight_rows.addWidget(CheckRow(check))

    def _update_actions(self):
        preflight = self.state.preflight_ok()
        self.inject_btn.setEnabled(preflight and self.state.any_selected())
        self.restore_btn.setEnabled(preflight)
        if not preflight:
            tip = "Clear the blocking preflight checks first."
        elif not self.state.any_selected():
            tip = "Select at least one option."
        else:
            tip = ""
        self.inject_btn.setToolTip(tip)
        self.restore_btn.setToolTip(
            "" if preflight else "Clear the blocking preflight checks first.")
