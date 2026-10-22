"""The design system: tokens first, then the stylesheet built from them.

One accent, used only for the primary action and live "on" state. Status marks
(pass/warn/fail) use neutral/amber/red, never the accent, so the accent keeps
its meaning. Spacing is a 4-pt scale, type is four sizes and two weights, and
there are three corner radii. Screens pull from these constants instead of
hard-coding values.
"""

# ---- Color -----------------------------------------------------------------
BG = "#0F1116"
BG_TOP = "#171A22"
PANEL = "#191C25"
PANEL_HI = "#212531"
BORDER = "#2A2F3B"
BORDER_HI = "#39404F"

ACCENT = "#7C83FF"
ACCENT_HI = "#969CFF"
ACCENT_DIM = "#333A7A"
ACCENT_FG = "#0A0B16"

AMBER = "#F3B13F"
RED = "#F06A6E"
NEUTRAL = "#888FA6"   # passed checks, idle dots - deliberately not the accent

TEXT = "#E9EBF3"
TEXT_DIM = "#9A9FB3"
TEXT_FAINT = "#656B80"

# ---- Spacing (4-pt grid) ---------------------------------------------------
SPACE = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48}


def sp(n: int) -> int:
    return SPACE[n]


# ---- Radius ----------------------------------------------------------------
R_CONTROL = 8
R_CARD = 12
R_HERO = 16

# ---- Type (4 sizes, 2 weights) --------------------------------------------
FS_DISPLAY = 26
FS_TITLE = 17
FS_BODY = 13
FS_SMALL = 11
W_REG = 400
W_MED = 600

SANS = '"SF Pro Text", "Helvetica Neue", "Segoe UI", system-ui, Arial, sans-serif'
MONO = '"SF Mono", "JetBrains Mono", "Menlo", "Monaco", monospace'

LEVEL_COLORS = {
    "INFO": TEXT_DIM,
    "STEP": TEXT,
    "OK": ACCENT,
    "WARN": AMBER,
    "ERROR": RED,
}

# status -> (color, icon name)
STATUS_STYLE = {
    "pass": (NEUTRAL, "check"),
    "warn": (AMBER, "warning"),
    "fail": (RED, "cross"),
    "checking": (TEXT_FAINT, "dots"),
}


def stylesheet() -> str:
    return f"""
    * {{ font-family: {SANS}; color: {TEXT}; outline: none; }}

    QWidget#rootWindow, QStackedWidget, QWidget#screen {{ background-color: {BG}; }}

    QFrame#card {{
        background-color: {PANEL};
        border: 1px solid {BORDER};
        border-radius: {R_CARD}px;
    }}
    QFrame#heroCard {{
        background-color: {PANEL_HI};
        border: 1px solid {BORDER_HI};
        border-radius: {R_HERO}px;
    }}
    QFrame#extraRow {{
        background-color: transparent;
        border: none;
        border-radius: {R_CONTROL}px;
    }}
    QFrame#extraRow:hover {{ background-color: {PANEL}; }}
    QFrame#topBar {{
        background-color: {PANEL};
        border: 1px solid {BORDER};
        border-radius: {R_CARD}px;
    }}

    QLabel#sectionLabel {{
        color: {TEXT_DIM}; font-size: {FS_SMALL}px; font-weight: {W_MED};
        letter-spacing: 1.2px;
    }}
    QLabel#title {{ color: {TEXT}; font-size: {FS_TITLE}px; font-weight: {W_MED}; }}
    QLabel#display {{ color: {TEXT}; font-size: {FS_DISPLAY}px; font-weight: 700; }}
    QLabel#subtitle {{ color: {TEXT_DIM}; font-size: {FS_BODY}px; }}
    QLabel#hint {{ color: {TEXT_FAINT}; font-size: {FS_SMALL}px; }}
    QLabel#metaMono {{ font-family: {MONO}; color: {TEXT_DIM}; font-size: {FS_SMALL}px; }}

    QPushButton {{
        background-color: {PANEL_HI};
        border: 1px solid {BORDER_HI};
        border-radius: {R_CONTROL}px;
        padding: 8px 14px;
        color: {TEXT}; font-size: {FS_BODY}px; font-weight: {W_MED};
    }}
    QPushButton:hover {{ border-color: {ACCENT_DIM}; background-color: {PANEL}; }}
    QPushButton:pressed {{ background-color: {BG}; }}
    QPushButton:focus {{ border-color: {ACCENT}; }}
    QPushButton:disabled {{ color: {TEXT_FAINT}; border-color: {BORDER}; background-color: {PANEL}; }}

    QPushButton#primary {{
        background-color: {ACCENT};
        color: {ACCENT_FG};
        border: 1px solid {ACCENT};
        border-radius: {R_CONTROL}px;
        padding: 12px 20px;
        font-size: {FS_TITLE}px; font-weight: 700;
    }}
    QPushButton#primary:hover {{ background-color: {ACCENT_HI}; border-color: {ACCENT_HI}; }}
    QPushButton#primary:pressed {{ background-color: #2FC77A; }}
    QPushButton#primary:focus {{ border: 2px solid {TEXT}; }}
    QPushButton#primary:disabled {{
        background-color: {PANEL}; color: {TEXT_FAINT}; border: 1px solid {BORDER};
    }}

    QPushButton#ghost {{ background-color: transparent; border: 1px solid {BORDER}; }}
    QPushButton#ghost:hover {{ background-color: {PANEL}; border-color: {BORDER_HI}; }}
    QPushButton#iconButton {{ background-color: transparent; border: none; padding: 6px; border-radius: {R_CONTROL}px; }}
    QPushButton#iconButton:hover {{ background-color: {PANEL_HI}; }}

    QPlainTextEdit#logBox {{
        background-color: #10141B;
        border: 1px solid {BORDER};
        border-radius: {R_CARD}px;
        color: {TEXT}; font-family: {MONO}; font-size: 12px;
        selection-background-color: {ACCENT_DIM};
        padding: {SPACE[2]}px;
    }}
    QLineEdit {{
        background-color: #10141B;
        border: 1px solid {BORDER};
        border-radius: {R_CONTROL}px;
        padding: 6px 10px; color: {TEXT}; font-size: {FS_BODY}px;
        selection-background-color: {ACCENT_DIM};
    }}
    QLineEdit:focus {{ border-color: {ACCENT_DIM}; }}

    QProgressBar {{
        background-color: {PANEL_HI}; border: 1px solid {BORDER};
        border-radius: 6px; height: 6px; text-align: center; color: {TEXT_DIM};
    }}
    QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 5px; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {BORDER_HI}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {ACCENT_DIM}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

    QMenuBar {{ background-color: {BG}; color: {TEXT_DIM}; }}
    QMenuBar::item {{ padding: 4px 10px; background: transparent; }}
    QMenuBar::item:selected {{ background-color: {PANEL_HI}; color: {TEXT}; }}
    QMenu {{ background-color: {PANEL}; border: 1px solid {BORDER}; padding: 4px; }}
    QMenu::item {{ padding: 6px 20px; border-radius: 6px; }}
    QMenu::item:selected {{ background-color: {PANEL_HI}; }}

    QDialog {{ background-color: {BG}; }}
    QLabel {{ background: transparent; }}
    QToolTip {{
        background-color: {PANEL}; color: {TEXT};
        border: 1px solid {BORDER_HI}; padding: 6px 8px; border-radius: 7px;
    }}
    """
