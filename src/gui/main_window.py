"""Main window: owns app state, drives the linear Connect -> Configure ->
Inject flow, the device watcher and the injection thread."""

import time

from PySide6.QtCore import Qt, QSettings, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget,
                               QGraphicsOpacityEffect, QMessageBox, QFileDialog)

from . import theme
from .app_state import AppState, ConnState, InjectState
from .workers import ConnectionWatcher, InjectThread, PreflightThread
from .screens.connect_screen import ConnectScreen
from .screens.configure_screen import ConfigureScreen
from .screens.inject_screen import InjectScreen
from .settings_dialog import SettingsDialog
from .dialogs import ConfirmDialog

PAGE_CONNECT = 0
PAGE_CONFIGURE = 1
PAGE_INJECT = 2


class MainWindow(QMainWindow):
    def __init__(self, device_manager):
        super().__init__()
        self.setObjectName("rootWindow")
        self.setWindowTitle("UnRestrict")
        self.dm = device_manager
        self.settings = QSettings("UnRestrict", "settings")
        self.state = AppState()
        self.inject_thread = None

        self.setStyleSheet(theme.stylesheet())
        self.resize(900, 620)
        self.setMinimumSize(820, 560)

        self.stack = QStackedWidget()
        self.stack.setObjectName("rootWindow")
        self.setCentralWidget(self.stack)

        self.connect_screen = ConnectScreen(self.state)
        self.configure_screen = ConfigureScreen(self.state)
        self.inject_screen = InjectScreen(self.state)
        for s in (self.connect_screen, self.configure_screen, self.inject_screen):
            self.stack.addWidget(s)

        # wiring
        self.connect_screen.proceed.connect(self._show_configure)
        self.configure_screen.inject_requested.connect(self._on_inject_requested)
        self.configure_screen.restore_requested.connect(self._on_restore_requested)
        self.configure_screen.settings_requested.connect(self._open_settings)
        self.inject_screen.back_requested.connect(self._show_connect)
        self.inject_screen.retry_requested.connect(self._retry)
        self.inject_screen.export_requested.connect(self._export_diagnostics)
        self.state.conn_changed.connect(self._on_conn_changed)
        self._last_mode = "apply"
        self._build_menu()

        # device watcher
        self.watcher = ConnectionWatcher(self.dm, self.settings)
        self.watcher.state.connect(self._on_watcher_state)
        self.watcher.start()

        # preflight re-runs while the Configure screen is up, so Find My and
        # battery clear themselves as the user fixes them.
        self.preflight_thread = None
        self.preflight_timer = QTimer(self)
        self.preflight_timer.setInterval(4000)
        self.preflight_timer.timeout.connect(self._run_preflight)

        self._show_connect()

    # ---- watcher -> state ----
    def _on_watcher_state(self, conn_state, info, error):
        self.state.set_conn(conn_state, info, error)

    def _on_conn_changed(self, conn_state):
        page = self.stack.currentIndex()
        if page == PAGE_CONNECT:
            self.connect_screen.render_state(
                conn_state, self.state.device_info, self.state.conn_error)
        elif page == PAGE_CONFIGURE:
            if conn_state != ConnState.CONNECTED:
                # device went away before injection -> return gracefully
                self._show_connect()
            else:
                self.configure_screen.refresh()

    # ---- navigation ----
    def _fade_in(self, widget: QWidget):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start()
        widget._fade_anim = anim  # keep a ref

    def _run_preflight(self):
        if self.preflight_thread is not None and self.preflight_thread.isRunning():
            return
        if self.state.conn_state != ConnState.CONNECTED:
            return
        self.preflight_thread = PreflightThread(self.dm)
        self.preflight_thread.done.connect(self._on_preflight_done)
        self.preflight_thread.start()

    def _on_preflight_done(self, checks):
        self.state.set_preflight(checks)
        if self.stack.currentIndex() == PAGE_CONFIGURE:
            self.configure_screen.refresh()

    def _show_connect(self):
        self.preflight_timer.stop()
        self.watcher.set_mode("full")
        self.state.set_inject(InjectState.IDLE)
        self.stack.setCurrentIndex(PAGE_CONNECT)
        self.connect_screen.render_state(
            self.state.conn_state, self.state.device_info, self.state.conn_error)
        self._fade_in(self.connect_screen)

    def _show_configure(self):
        # only advance if actually connected
        if self.state.conn_state != ConnState.CONNECTED:
            return
        self.watcher.set_mode("presence")
        self.state.set_preflight([])  # show "checking" until the first run lands
        self.configure_screen.refresh()
        self.stack.setCurrentIndex(PAGE_CONFIGURE)
        self._fade_in(self.configure_screen)
        self._run_preflight()
        self.preflight_timer.start()

    # ---- inject / restore ----
    def _on_inject_requested(self):
        if not self.state.preflight_ok() or not self.state.any_selected():
            return
        dry = self.state.dry_run
        dlg = ConfirmDialog(
            header="Dry run (nothing sent)" if dry else "Apply these changes?",
            lines=self.state.summary_lines(),
            warning=("This is a dry run: the payload is built and logged, but "
                     "nothing is sent to your device." if dry else
                     "Your iPhone will restart to apply the changes. Keep it "
                     "connected and do not unplug it."),
            confirm_label="Dry Run" if dry else "Inject",
            icon_name="bolt", warn_level="dim" if dry else "amber", parent=self)
        if dlg.exec() == ConfirmDialog.Accepted:
            self._start_run("apply")

    def _on_restore_requested(self):
        if not self.state.preflight_ok():
            return
        dry = self.state.dry_run
        dlg = ConfirmDialog(
            header="Dry run restore (nothing sent)" if dry else "Restore defaults?",
            lines=["Re-enables every daemon UnRestrict can disable",
                   "Screen Time, Location, Game Center, logs and the rest start "
                   "working again"],
            warning=("Dry run: the restore payload is built and logged only." if dry
                     else "Your iPhone will restart. Note: Screen Time limits that "
                     "were erased can't be recovered, but Screen Time itself will "
                     "work again."),
            confirm_label="Dry Run" if dry else "Restore",
            icon_name="shield", warn_level="dim" if dry else "amber", parent=self)
        if dlg.exec() == ConfirmDialog.Accepted:
            self._start_run("restore")

    def _retry(self):
        self._start_run(self._last_mode)

    def _start_run(self, mode: str):
        if self.inject_thread is not None and self.inject_thread.isRunning():
            return  # guard against double start
        self._last_mode = mode
        # stop the watcher and preflight so they don't contend for lockdown
        self.watcher.set_mode("presence")
        self.preflight_timer.stop()

        self.state.set_inject(InjectState.RUNNING)
        self.stack.setCurrentIndex(PAGE_INJECT)
        self._fade_in(self.inject_screen)
        self.inject_screen.begin(self.state.dry_run, mode=mode)

        from .log_bus import log_step, log_info
        if mode == "restore":
            log_step("Starting restore (re-enabling daemons)")
        else:
            count = self.state.build_tweaks()
            log_step("Starting UnRestrict run")
            log_info(f"{count} daemon process(es) selected across "
                     f"{len(self.state.selected_options())} option(s).")

        self.inject_thread = InjectThread(
            self.dm, self.state.dry_run, mode=mode, settings=self.settings,
            device_info=self.state.device_info,
            options=(self.state.summary_lines() if mode == "apply"
                     else ["Restore defaults"]))
        self.inject_thread.finished_alert.connect(self._on_inject_done)
        self.inject_thread.start()

    def _on_inject_done(self, msg):
        success = (msg is not None
                   and getattr(msg, "icon", None) == QMessageBox.Information)
        message = getattr(msg, "txt", "") if msg else "No result."
        detail = getattr(msg, "detailed_txt", None) if msg else None

        from .log_bus import log_ok, log_error
        if success:
            log_ok(message.replace("\n", " "))
            self.state.set_inject(InjectState.DONE)
            if self.state.dry_run:
                nxt = "Dry run finished. Nothing was sent to your device."
            elif self._last_mode == "restore":
                nxt = ("Your device is rebooting. The disabled daemons have been "
                       "re-enabled. Remember to turn Find My back on.")
            else:
                nxt = ("Your device is rebooting. Wait for it to finish, then you "
                       "can reconnect it. Remember to turn Find My back on.")
            self.inject_screen.finish(True, message, nxt)
        else:
            log_error(message.replace("\n", " "))
            self.state.set_inject(InjectState.FAILED)
            self.inject_screen.finish(False, message, detail or "")

    # ---- menu / settings ----
    def _build_menu(self):
        bar = self.menuBar()
        app_menu = bar.addMenu("UnRestrict")
        prefs = QAction("Settings…", self)
        prefs.setShortcut(QKeySequence.Preferences)  # Cmd+,
        prefs.triggered.connect(self._open_settings)
        app_menu.addAction(prefs)
        quit_action = QAction("Quit UnRestrict", self)
        quit_action.setShortcut(QKeySequence.Quit)   # Cmd+Q
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

        log_menu = bar.addMenu("Log")
        find = QAction("Find in Log", self)
        find.setShortcut(QKeySequence.Find)          # Cmd+F
        find.triggered.connect(
            lambda: self.inject_screen.search.setFocus())
        log_menu.addAction(find)

    def _open_settings(self):
        SettingsDialog(self.state, self.dm, parent=self).exec()
        self.configure_screen.refresh()

    def _export_diagnostics(self, text):
        default = time.strftime("unrestrict-diagnostics-%Y%m%d-%H%M%S.txt")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export diagnostics", default, "Text files (*.txt)")
        if path:
            from src.controllers.run_record import export_diagnostics
            export_diagnostics(path, text, redact_udid=True)

    # ---- safety: block close mid-run ----
    def closeEvent(self, event):
        if self.state.inject_state == InjectState.RUNNING:
            resp = QMessageBox.warning(
                self, "Injection in progress",
                "A change is being applied to your device. Quitting now could "
                "leave it in a bad state.\n\nQuit anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if resp != QMessageBox.Yes:
                event.ignore()
                return
        try:
            self.watcher.stop()
            self.watcher.wait(1500)
        except Exception:
            pass
        event.accept()
