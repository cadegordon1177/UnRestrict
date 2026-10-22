"""Preflight checks run against a connected device before an injection.

Kept lean on purpose: Find My (the one that can brick a restore if left on),
a supported iOS version, a trusted/paired session, and enough battery to
survive the reboot. Each check is defensive - a probe the OS doesn't support
returns "unknown" instead of raising.

Find My has no reliable proactive getter across iOS versions; the read here is
best-effort and the restore itself still refuses to run while Find My is on,
which is the real enforcement.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.diagnostics import DiagnosticsService

from .constants import MIN_VERSION, MAX_VERSION

# Battery thresholds (percent): block below the first, warn below the second.
BATTERY_BLOCK = 15
BATTERY_WARN = 30


class Status(Enum):
    CHECKING = "checking"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class Check:
    key: str
    label: str
    status: Status
    detail: str = ""
    fix: str = ""
    blocking: bool = True


def _battery_percent(info: dict) -> Optional[int]:
    if not info:
        return None
    current = info.get("CurrentCapacity")
    maximum = info.get("MaxCapacity") or 100
    if current is None:
        return None
    try:
        return round(current / maximum * 100) if maximum else int(current)
    except (TypeError, ZeroDivisionError):
        return None


async def _read_find_my(ld) -> Optional[bool]:
    """Best-effort: True=on, False=off, None=could not determine."""
    for domain, key in (("com.apple.fmip", "IsAssociated"), ("com.apple.fmip", None)):
        try:
            value = await ld.get_value(domain, key)
        except Exception:
            continue
        if isinstance(value, bool):
            return value
        if isinstance(value, dict):
            for k in ("IsAssociated", "Associated", "Enabled", "activated"):
                if isinstance(value.get(k), bool):
                    return value[k]
    return None


async def run_checks(udid: str, device) -> list[Check]:
    checks: list[Check] = []

    ld = None
    try:
        ld = await create_using_usbmux(serial=udid)
    except Exception as e:
        checks.append(Check("trust", "Device trusted and paired", Status.FAIL,
                            detail=str(e),
                            fix="Unlock the iPhone and tap Trust, then enter "
                                "your passcode."))
        return checks

    find_my = await _read_find_my(ld)
    if find_my is True:
        checks.append(Check("find_my", "Find My is off", Status.FAIL,
                            detail="Find My is on",
                            fix="Settings > [your name] > Find My > Find My "
                                "iPhone > off. This clears on its own."))
    elif find_my is False:
        checks.append(Check("find_my", "Find My is off", Status.PASS))
    else:
        checks.append(Check(
            "find_my", "Find My is off", Status.WARN,
            detail="couldn't verify automatically", blocking=False,
            fix="Turn Find My off (Settings > [your name] > Find My). The "
                "injection refuses to run while it's on."))

    supported = device.supported()
    checks.append(Check("ios", "iOS version supported",
                        Status.PASS if supported else Status.FAIL,
                        detail=f"iOS {device.version}",
                        fix=f"Supported range is {MIN_VERSION}-{MAX_VERSION}."))

    checks.append(Check("trust", "Device trusted and paired", Status.PASS))

    try:
        pct = _battery_percent(await DiagnosticsService(ld).get_battery())
    except Exception:
        pct = None
    if pct is None:
        checks.append(Check("battery", "Battery level", Status.WARN,
                            detail="couldn't read", blocking=False))
    elif pct < BATTERY_BLOCK:
        checks.append(Check("battery", "Battery level", Status.FAIL,
                            detail=f"{pct}%",
                            fix="Charge above 15% before injecting."))
    elif pct < BATTERY_WARN:
        checks.append(Check("battery", "Battery level", Status.WARN,
                            detail=f"{pct}%", blocking=False,
                            fix="Below 30% - charge first if you can."))
    else:
        checks.append(Check("battery", "Battery level", Status.PASS,
                            detail=f"{pct}%"))

    try:
        await ld.close()
    except Exception:
        pass
    return checks


def run_checks_sync(udid: str, device) -> list[Check]:
    return asyncio.run(run_checks(udid, device))
