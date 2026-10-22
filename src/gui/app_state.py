"""Central application state.

Screens react to state changes through signals here instead of calling each
other directly. Also owns the feature catalog (the hero option + extras) and
the single place that maps user selections onto the existing daemon tweaks.
"""

from enum import Enum

from PySide6.QtCore import QObject, Signal

from src.tweaks.tweaks import tweaks, TweakID
from src.tweaks.tweak_loader import load_daemons
from src.tweaks.daemons_tweak import Daemon


# Baseline daemons always written into disabled.plist. We reset to this
# before layering the user's selections, so repeated runs never accumulate
# stale entries.
DEFAULT_DISABLED_DAEMONS = {
    "com.apple.magicswitchd.companion": True,
    "com.apple.security.otpaird": True,
    "com.apple.dhcp6d": True,
    "com.apple.bootpd": True,
    "com.apple.ftp-proxy-embedded": False,
    "com.apple.relevanced": True,
}


class Option:
    def __init__(self, oid, title, desc, group, daemons=None,
                 clear_screentime=False, default_on=False, hero=False):
        self.id = oid
        self.title = title
        self.desc = desc
        self.group = group
        self.daemons = daemons or []
        self.clear_screentime = clear_screentime
        self.default_on = default_on
        self.hero = hero


# The hero option maps to the three Screen Time actions from the PRD.
HERO_OPTION = Option(
    "screen_time",
    "Remove Screen Time",
    "Disables the Screen Time and usage-tracking daemons and wipes the Screen "
    "Time database, so limits, downtime and app restrictions stop working.",
    group="Screen Time",
    daemons=[Daemon.UsageTrackingAgent, Daemon.ScreenTime],
    clear_screentime=True,
    default_on=True,
    hero=True,
)

EXTRA_OPTIONS = [
    Option("crash", "Disable Logs, Dumps & Crash Reports",
           "Stops the logging, crash-report and diagnostic daemons.",
           group="System", daemons=[Daemon.CrashReports, Daemon.Diagnostics]),
    Option("gamecenter", "Disable Game Center",
           "Stops the Game Center daemon (gamed).",
           group="System", daemons=[Daemon.GameCenter]),
    Option("tips", "Disable Tips Services",
           "Stops the Tips daemon (tipsd).",
           group="System", daemons=[Daemon.Tips]),
    Option("followup", "Disable FollowUp",
           "Stops the FollowUp daemon (followupd) used for setup reminders.",
           group="Privacy", daemons=[Daemon.FollowUp]),
    Option("location", "Disable Location Services",
           "Stops locationd. Maps, Find My and location features stop working.",
           group="Privacy", daemons=[Daemon.Location]),
    Option("vpn", "Disable VPN Service",
           "Stops the legacy VPN daemon (racoon).",
           group="Privacy", daemons=[Daemon.VPN]),
]

ALL_OPTIONS = [HERO_OPTION] + EXTRA_OPTIONS


class ConnState(Enum):
    WAITING = "waiting"          # no device plugged in
    LOCKED = "locked"            # present but locked / not trusted
    CONNECTED = "connected"      # ready
    UNSUPPORTED = "unsupported"  # iOS version out of range
    ERROR = "error"


class InjectState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AppState(QObject):
    conn_changed = Signal(object)       # ConnState
    inject_changed = Signal(object)     # InjectState
    options_changed = Signal()
    preflight_changed = Signal()

    def __init__(self):
        super().__init__()
        self.conn_state = ConnState.WAITING
        self.inject_state = InjectState.IDLE
        self.device_info = {}           # name/version/build/model/udid/usb
        self.conn_error = ""
        self.dry_run = False
        self.preflight = []             # list[preflight.Check]
        self.selected = {o.id: o.default_on for o in ALL_OPTIONS}

    def set_preflight(self, checks):
        self.preflight = checks
        self.preflight_changed.emit()

    def preflight_ok(self) -> bool:
        """True when no blocking check is failing (checks must have run)."""
        from src.devicemanagement.preflight import Status
        if not self.preflight:
            return False
        return not any(c.blocking and c.status == Status.FAIL
                       for c in self.preflight)

    # ---- connection ----
    def set_conn(self, state: ConnState, info=None, error=""):
        changed = (state != self.conn_state) or (info is not None and info != self.device_info)
        self.conn_state = state
        if info is not None:
            self.device_info = info
        self.conn_error = error
        if changed:
            self.conn_changed.emit(state)

    # ---- injection ----
    def set_inject(self, state: InjectState):
        self.inject_state = state
        self.inject_changed.emit(state)

    # ---- options ----
    def toggle(self, oid: str, value: bool):
        self.selected[oid] = value
        self.options_changed.emit()

    def any_selected(self) -> bool:
        return any(self.selected.values())

    def selected_options(self):
        return [o for o in ALL_OPTIONS if self.selected.get(o.id)]

    def summary_lines(self):
        """Human-readable list of what will be applied (for the confirm sheet)."""
        return [o.title for o in self.selected_options()]

    # ---- the one place selections become daemon tweaks ----
    def build_tweaks(self):
        """Configure the shared `tweaks` dict from the current selection.

        Returns the number of distinct daemon processes that will be disabled.
        """
        load_daemons()
        daemons_tweak = tweaks[TweakID.Daemons]            # AdvancedPlistTweak
        screentime_tweak = tweaks[TweakID.ClearScreenTimeAgentPlist]  # NullifyFileTweak

        # fresh baseline each run
        daemons_tweak.value = dict(DEFAULT_DISABLED_DAEMONS)
        daemons_tweak.enabled = False
        screentime_tweak.enabled = False

        procs = set()
        for opt in self.selected_options():
            for daemon in opt.daemons:
                daemons_tweak.set_multiple_values(daemon.value, True)
                procs.update(daemon.value)
            if opt.clear_screentime:
                screentime_tweak.enabled = True

        # The "Modify daemons" flag: enable the tweak whenever anything is set.
        daemons_tweak.enabled = len(procs) > 0
        return len(procs)
