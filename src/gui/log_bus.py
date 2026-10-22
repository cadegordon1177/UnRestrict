"""Signal-based logging for the live log box.

Everything that should appear in the terminal-style log box goes through the
single global `log_bus`. Worker threads emit into it via Qt signals, so the
UI never touches worker state directly and never freezes.

Three sources feed the bus:
  1. Explicit calls: log_step(), log_ok(), log_warn(), log_error(), log_info().
  2. `print()` output from the backend (device_manager uses print()).
  3. The `pymobiledevice3` / root logging output (real device activity).
"""

import logging
import sys
import time

from PySide6.QtCore import QObject, Signal


class LogLine:
    __slots__ = ("ts", "level", "msg")

    def __init__(self, level: str, msg: str):
        self.ts = time.strftime("%H:%M:%S")
        self.level = level
        self.msg = msg

    def formatted(self) -> str:
        return f"[{self.ts}] [{self.level}] {self.msg}"


class LogBus(QObject):
    # emitted for every line; the log box renders it with level coloring
    line = Signal(object)  # LogLine

    def emit_line(self, level: str, msg: str):
        for part in str(msg).splitlines() or [""]:
            if part.strip() == "":
                continue
            self.line.emit(LogLine(level, part))


# single global instance
log_bus = LogBus()


def log_info(msg: str):
    log_bus.emit_line("INFO", msg)


def log_step(msg: str):
    log_bus.emit_line("STEP", msg)


def log_ok(msg: str):
    log_bus.emit_line("OK", msg)


def log_warn(msg: str):
    log_bus.emit_line("WARN", msg)


def log_error(msg: str):
    log_bus.emit_line("ERROR", msg)


class _StreamTee:
    """Mirror a stream (stdout/stderr) into the log bus while preserving it."""

    def __init__(self, original, level: str):
        self._original = original
        self._level = level
        self._buffer = ""

    def write(self, text):
        try:
            if self._original is not None:
                self._original.write(text)
        except Exception:
            pass
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                log_bus.emit_line(self._level, line)

    def flush(self):
        try:
            if self._original is not None:
                self._original.flush()
        except Exception:
            pass

    def isatty(self):
        return False


class _BusLogHandler(logging.Handler):
    """Route Python logging records (e.g. pymobiledevice3) into the bus."""

    _LEVEL_MAP = {
        logging.CRITICAL: "ERROR",
        logging.ERROR: "ERROR",
        logging.WARNING: "WARN",
        logging.INFO: "INFO",
        logging.DEBUG: "INFO",
    }

    def emit(self, record):
        try:
            level = self._LEVEL_MAP.get(record.levelno, "INFO")
            msg = self.format(record)
            log_bus.emit_line(level, msg)
        except Exception:
            pass


_installed = False


def install_capture():
    """Tee stdout/stderr and attach a logging handler. Idempotent."""
    global _installed
    if _installed:
        return
    _installed = True

    sys.stdout = _StreamTee(sys.stdout, "INFO")
    sys.stderr = _StreamTee(sys.stderr, "WARN")

    handler = _BusLogHandler()
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    root = logging.getLogger()
    # keep whatever level is set, but make sure records reach us
    if root.level == logging.NOTSET or root.level > logging.INFO:
        root.setLevel(logging.INFO)
    root.addHandler(handler)
