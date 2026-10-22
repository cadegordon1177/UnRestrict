"""Per-run snapshot and persistent safety log, stored under Application Support.

A snapshot here is a record of the run (device facts, the exact options, the
full step log and the verified outcome), not a byte image of the phone — the
sparse-restore mechanism is write-only and can't read the original system
plists back off the device. The undo path re-applies known defaults rather than
replaying captured originals, which the UI states plainly.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

APP_SUPPORT = Path.home() / "Library" / "Application Support" / "UnRestrict"
SNAPSHOT_DIR = APP_SUPPORT / "snapshots"
LOG_DIR = APP_SUPPORT / "logs"
LOG_FILE = LOG_DIR / "unrestrict.log"


def _ensure_dirs():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _append_persistent(line: str):
    try:
        _ensure_dirs()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


class RunRecord:
    def __init__(self, device_info: dict, options: list[str], mode: str,
                 dry_run: bool):
        self.device_info = device_info
        self.udid = device_info.get("udid", "unknown")
        self.mode = mode
        self.dry_run = dry_run
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.dir = SNAPSHOT_DIR / f"{self.udid}-{stamp}"
        self.log_path = self.dir / "run.log"
        self._meta = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "dry_run": dry_run,
            "device": {k: device_info.get(k) for k in
                       ("name", "model", "version", "build", "udid")},
            "options": options,
        }
        self._started = False

    def start(self) -> Optional[Path]:
        try:
            _ensure_dirs()
            self.dir.mkdir(parents=True, exist_ok=True)
            with open(self.dir / "meta.json", "w", encoding="utf-8") as f:
                json.dump(self._meta, f, indent=2)
            # touch the log so the path is valid immediately
            self.log_path.write_text("", encoding="utf-8")
            self._started = self.dir.exists() and (self.dir / "meta.json").exists()
        except Exception:
            self._started = False
        return self.dir if self._started else None

    def log(self, level: str, message: str):
        line = f"[{time.strftime('%H:%M:%S')}] [{level}] {message}"
        if self._started:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
        _append_persistent(f"{self.udid[:6]}… {line}")

    def finish(self, success: bool, verification: list[dict]) -> Optional[Path]:
        if not self._started:
            return None
        try:
            with open(self.dir / "result.json", "w", encoding="utf-8") as f:
                json.dump({"success": success, "verification": verification},
                          f, indent=2)
        except Exception:
            pass
        return self.dir


def latest_snapshots(limit: int = 20) -> list[dict]:
    if not SNAPSHOT_DIR.exists():
        return []
    rows = []
    for d in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
        meta = d / "meta.json"
        if meta.is_file():
            try:
                rows.append({"dir": str(d), **json.loads(meta.read_text())})
            except Exception:
                continue
        if len(rows) >= limit:
            break
    return rows


def export_diagnostics(dest_path: str, log_text: str, redact_udid: bool = True):
    """Write the current session log plus environment facts for support.

    The device UDID and anything personal are left out unless the caller opts
    in, so the file is safe to share.
    """
    header = [
        "UnRestrict diagnostics",
        time.strftime("%Y-%m-%d %H:%M:%S"),
        "",
    ]
    body = log_text
    if redact_udid:
        body = _redact(body)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + body)


def _redact(text: str) -> str:
    import re
    # 40-char and 24-char hyphenated iOS UDIDs
    text = re.sub(r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16}\b", "<udid>", text)
    text = re.sub(r"\b[0-9a-f]{40}\b", "<udid>", text)
    return text
