"""Background threads: device auto-detection and the injection run.

Both use Qt signals so the UI thread is never blocked and log lines stream in
real time.
"""

import asyncio
import subprocess
import time

from PySide6.QtCore import QThread, Signal

from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux

from src.devicemanagement.constants import MIN_VERSION, MAX_VERSION
from src.devicemanagement import preflight
from src.controllers.run_record import RunRecord
from .app_state import ConnState
from .log_bus import log_step, log_ok, log_warn, log_error, log_info


class ConnectionWatcher(QThread):
    """Polls for a connected device and reports a ConnState.

    mode 'full'     : fully probe + populate the DeviceManager (Connect screen)
    mode 'presence' : cheap presence check to notice a disconnect
    """

    state = Signal(object, object, str)  # ConnState, info|None, error

    def __init__(self, dm, settings, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.settings = settings
        self._running = True
        self._mode = "full"
        self._last_alert = None

    def set_mode(self, mode: str):
        self._mode = mode

    def stop(self):
        self._running = False

    def _capture_alert(self, msg):
        self._last_alert = msg

    def _list_present(self):
        try:
            devices = asyncio.run(usbmux.list_devices())
        except Exception:
            return None  # usbmuxd unreachable
        wifi_ok = self.dm.pref_manager.apply_over_wifi
        return [d for d in devices if d.is_usb or wifi_ok]

    def _probe(self):
        present = self._list_present()
        if present is None:
            return ConnState.ERROR, None, "Could not reach the device service (usbmuxd)."
        if len(present) == 0:
            self.dm.set_current_device(None)
            return ConnState.WAITING, None, ""

        if self._mode == "presence":
            # device still physically present; don't re-pair every tick
            return ConnState.CONNECTED, None, ""

        # full probe: populate the DeviceManager
        self._last_alert = None
        try:
            self.dm.get_devices(self.settings, self._capture_alert)
        except Exception as e:
            return ConnState.ERROR, None, str(e)

        dev = self.dm.data_singleton.current_device
        if dev is None:
            # present but we couldn't talk to it -> locked / not trusted
            return ConnState.LOCKED, None, ""

        info = {
            "name": dev.name,
            "version": dev.version,
            "build": dev.build,
            "model": dev.model,
            "udid": dev.udid,
            "usb": dev.connected_via_usb,
        }
        if not self.dm.get_current_device_supports_restore():
            return ConnState.UNSUPPORTED, info, (
                f"iOS {dev.version} is outside the supported range "
                f"({MIN_VERSION} - {MAX_VERSION})."
            )
        return ConnState.CONNECTED, info, ""

    def run(self):
        while self._running:
            try:
                state, info, err = self._probe()
                self.state.emit(state, info, err)
            except Exception as e:
                self.state.emit(ConnState.ERROR, None, str(e))
            # poll roughly every ~1.6s, but stay responsive to stop()
            for _ in range(16):
                if not self._running:
                    break
                self.msleep(100)


class PreflightThread(QThread):
    """Runs the preflight checks against the current device, off the UI thread."""

    done = Signal(object)  # list[preflight.Check]

    def __init__(self, dm, parent=None):
        super().__init__(parent)
        self.dm = dm

    def run(self):
        device = getattr(self.dm.data_singleton, "current_device", None)
        if device is None:
            self.done.emit([])
            return
        try:
            checks = preflight.run_checks_sync(device.udid, device)
        except Exception as e:
            log_warn(f"Preflight could not complete: {e}")
            checks = []
        self.done.emit(checks)


def _start_keep_awake():
    """Hold the Mac awake for the duration of a run (macOS `caffeinate`)."""
    try:
        return subprocess.Popen(["caffeinate", "-dimsu"])
    except Exception:
        return None


def _stop_keep_awake(proc):
    if proc is not None:
        try:
            proc.terminate()
        except Exception:
            pass


class InjectThread(QThread):
    """Runs an apply or a restore, logging every phase to the bus.

    mode 'apply'   : disable the selected daemons (DeviceManager.apply_changes)
    mode 'restore' : write the baseline disabled.plist to re-enable everything
                     UnRestrict can disable (DeviceManager.reset_tweaks).
    """

    finished_alert = Signal(object)  # ApplyAlertMessage

    def __init__(self, dm, dry_run: bool, mode: str = "apply",
                 settings=None, device_info=None, options=None, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.dry_run = dry_run
        self.mode = mode
        self.settings = settings
        self.device_info = device_info or {}
        self.options = options or []
        self.record = None

    def _update_label(self, txt: str):
        if txt is None or txt == "sudo_pwd":
            return
        clean = txt.replace("\n", " ")
        log_step(clean)
        if self.record is not None:
            self.record.log("STEP", clean)

    def _show_alert(self, msg):
        self.finished_alert.emit(msg)

    def run(self):
        self.dm.dry_run = self.dry_run
        self.record = RunRecord(self.device_info, self.options, self.mode,
                                self.dry_run)
        path = self.record.start()
        if path is not None:
            log_info(f"Snapshot/log folder: {path}")
        else:
            log_warn("Could not create the snapshot folder; continuing.")
        if self.dry_run:
            log_info("Dry run enabled - the payload will be built but NOT sent.")

        keep_awake = None if self.dry_run else _start_keep_awake()
        alert = None
        try:
            # apply_changes / reset_tweaks always call show_alert in their
            # finally block, so finished_alert always fires. Capture it here
            # too so we can verify afterwards.
            def capture(msg):
                nonlocal alert
                alert = msg
                self._show_alert(msg)

            if self.mode == "restore":
                self.dm.restore_defaults(self._update_label, capture)
            else:
                self.dm.apply_changes(self._update_label, capture)
        except Exception as e:
            log_error(f"Unexpected failure: {type(e).__name__}: {e}")
            from src.gui.thread_workers.apply_worker import ApplyAlertMessage
            alert = ApplyAlertMessage(txt=f"{type(e).__name__}: {e}", title="Error!")
            self.finished_alert.emit(alert)
        finally:
            _stop_keep_awake(keep_awake)
            self.dm.dry_run = False

        self._record_outcome(alert)

    def _record_outcome(self, alert):
        from PySide6.QtWidgets import QMessageBox
        success = (alert is not None
                   and getattr(alert, "icon", None) == QMessageBox.Information)
        verification = []
        if success and not self.dry_run:
            verification = self._verify()
        if self.record is not None:
            self.record.finish(success, verification)

    def _verify(self):
        """After the reboot, confirm the device comes back (not bricked).

        Per-option daemon state isn't directly queryable over lockdown, so each
        option is recorded as applied-but-unverified; the real safety signal is
        that the device reconnects and isn't stuck in a boot loop.
        """
        log_step("Verifying: waiting for the device to reconnect...")
        udid = self.device_info.get("udid")
        reconnected = self._wait_for_reconnect(udid, timeout=90)
        if reconnected:
            log_ok("Device reconnected after reboot.")
        else:
            log_warn("Device did not reconnect within 90s - check it manually.")
        results = [{"option": o, "verified": False,
                    "note": "applied; daemon state not directly detectable"}
                   for o in self.options]
        for o in self.options:
            log_info(f"{o}: applied (not independently verifiable)")
        results.append({"option": "device_reconnected", "verified": reconnected,
                        "note": "device responded after reboot"})
        return results

    def _wait_for_reconnect(self, udid, timeout):
        if not udid:
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ld = asyncio.run(create_using_usbmux(serial=udid))
                asyncio.run(ld.close())
                return True
            except Exception:
                time.sleep(2)
        return False
