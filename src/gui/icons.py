"""Custom thin-line SVG icon set for UnRestrict.

Icons are defined as SVG templates with a `{c}` placeholder for stroke color
so a single definition serves any accent/state color. Rendered to QIcon /
QPixmap on demand.
"""

from PySide6.QtCore import QByteArray, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from . import theme

# All icons share a 24x24 viewbox, 1.6 stroke, round caps - a consistent
# thin line style. `{c}` is replaced with the desired color.
_ICONS = {
    "phone": """
        <rect x="6" y="2.5" width="12" height="19" rx="2.6" fill="none" stroke="{c}" stroke-width="1.5"/>
        <line x1="10.5" y1="18.3" x2="13.5" y2="18.3" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
    """,
    "shield": """
        <path d="M12 2.5l7 3v5.5c0 4.6-3 8.3-7 10-4-1.7-7-5.4-7-10V5.5z" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/>
        <path d="M8.8 12l2.2 2.2 4.2-4.6" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "terminal": """
        <rect x="3" y="4" width="18" height="16" rx="2.4" fill="none" stroke="{c}" stroke-width="1.5"/>
        <path d="M7 9l3 3-3 3" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="12.5" y1="15.5" x2="16.5" y2="15.5" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
    """,
    "bolt": """
        <path d="M13 2.5L5 13h6l-1 8.5L19 10h-6z" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/>
    """,
    "gear": """
        <circle cx="12" cy="12" r="3.1" fill="none" stroke="{c}" stroke-width="1.5"/>
        <path d="M12 2.6v2.3M12 19.1v2.3M4.4 7.2l2 1.1M17.6 15.7l2 1.1M4.4 16.8l2-1.1M17.6 8.3l2-1.1" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
    """,
    "check": """
        <path d="M4.5 12.5l4.5 4.5L19.5 6.5" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "warning": """
        <path d="M12 3.5L21 19H3z" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/>
        <line x1="12" y1="9.5" x2="12" y2="14" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>
        <circle cx="12" cy="16.6" r="0.9" fill="{c}"/>
    """,
    "cross": """
        <path d="M6 6l12 12M18 6L6 18" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>
    """,
    "copy": """
        <rect x="8" y="8" width="11" height="12" rx="2" fill="none" stroke="{c}" stroke-width="1.5"/>
        <path d="M5 15.5V5a2 2 0 0 1 2-2h8.5" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
    """,
    "save": """
        <path d="M5 4h11l3 3v13H5z" fill="none" stroke="{c}" stroke-width="1.5" stroke-linejoin="round"/>
        <rect x="8.5" y="4" width="6" height="4.5" fill="none" stroke="{c}" stroke-width="1.3"/>
        <rect x="8" y="12.5" width="8" height="5.5" fill="none" stroke="{c}" stroke-width="1.3"/>
    """,
    "lock": """
        <rect x="5.5" y="10.5" width="13" height="9.5" rx="2.2" fill="none" stroke="{c}" stroke-width="1.5"/>
        <path d="M8.3 10.5V7.8a3.7 3.7 0 0 1 7.4 0" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
        <circle cx="12" cy="15" r="1.3" fill="{c}"/>
    """,
    "unlock": """
        <rect x="5.5" y="10.5" width="13" height="9.5" rx="2.2" fill="none" stroke="{c}" stroke-width="1.5"/>
        <path d="M8.3 10.5V7.8a3.7 3.7 0 0 1 7.1-1.4" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>
        <circle cx="12" cy="15" r="1.3" fill="{c}"/>
    """,
    "back": """
        <path d="M14.5 6l-6 6 6 6" fill="none" stroke="{c}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "dots": """
        <circle cx="5.5" cy="12" r="1.6" fill="{c}"/>
        <circle cx="12" cy="12" r="1.6" fill="{c}"/>
        <circle cx="18.5" cy="12" r="1.6" fill="{c}"/>
    """,
    "search": """
        <circle cx="11" cy="11" r="6.3" fill="none" stroke="{c}" stroke-width="1.6"/>
        <line x1="15.6" y1="15.6" x2="20" y2="20" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/>
    """,
}


def _svg_markup(name: str, color: str) -> str:
    body = _ICONS[name].format(c=color)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f"{body}</svg>"
    )


def svg_pixmap(name: str, color: str = theme.TEXT, size: int = 24) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(_svg_markup(name, color).encode("utf-8")))
    # render at 2x for crisp hidpi
    scale = 2
    pm = QPixmap(size * scale, size * scale)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(scale)
    return pm


def svg_icon(name: str, color: str = theme.TEXT, size: int = 24) -> QIcon:
    return QIcon(svg_pixmap(name, color, size))


# Large hero phone used on the Connect screen. Realistic iPhone proportions
# (~1:2.05). The inner glyph is centered at (70,124) and changes with state,
# so "waiting" shows no checkmark.
_PHONE_GLYPHS = {
    "none": "",
    "check": (
        '<path d="M55 124 l11 11 l23 -27" fill="none" stroke="{c}" '
        'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    "dots": (
        '<circle cx="55" cy="124" r="5" fill="{c}"/>'
        '<circle cx="70" cy="124" r="5" fill="{c}"/>'
        '<circle cx="85" cy="124" r="5" fill="{c}"/>'
    ),
    "lock": (
        '<rect x="56" y="122" width="28" height="21" rx="4" fill="none" '
        'stroke="{c}" stroke-width="2.6"/>'
        '<path d="M61 122 v-6 a9 9 0 0 1 18 0 v6" fill="none" '
        'stroke="{c}" stroke-width="2.6" stroke-linecap="round"/>'
    ),
    "cross": (
        '<path d="M60 114 l20 20 M80 114 l-20 20" stroke="{c}" '
        'stroke-width="3" stroke-linecap="round"/>'
    ),
}


def phone_markup(color: str, glyph: str = "none") -> bytes:
    inner = _PHONE_GLYPHS.get(glyph, "").format(c=color)
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 248">
  <rect x="15" y="12" width="110" height="224" rx="30" fill="none"
        stroke="{color}" stroke-width="2.6"/>
  <rect x="23" y="22" width="94" height="204" rx="22" fill="none"
        stroke="{color}" stroke-width="1" opacity="0.26"/>
  <rect x="60" y="18" width="20" height="4.5" rx="2.25" fill="{color}" opacity="0.5"/>
  {inner}
</svg>
"""
    return svg.encode("utf-8")


def app_icon_svg(size: int = 512) -> str:
    """The UnRestrict app glyph: dark rounded square + neon unlocked padlock."""
    a = theme.ACCENT
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <radialGradient id="g" cx="50%" cy="38%" r="75%">
      <stop offset="0%" stop-color="#13261B"/>
      <stop offset="100%" stop-color="#0A0C0B"/>
    </radialGradient>
  </defs>
  <rect x="26" y="26" width="460" height="460" rx="112" fill="url(#g)"
        stroke="{theme.BORDER}" stroke-width="4"/>
  <g stroke="{a}" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="156" y="236" width="200" height="150" rx="34" stroke-width="20"/>
    <path d="M196 236 v-44 a60 60 0 0 1 112 -26" stroke-width="20"/>
  </g>
  <circle cx="256" cy="306" r="22" fill="{a}"/>
  <rect x="246" y="320" width="20" height="40" rx="10" fill="{a}"/>
</svg>
"""
