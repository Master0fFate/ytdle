"""Google Material Icons Outlined glyphs for the YTDLE desktop chrome.

Material Icons (https://github.com/google/material-design-icons) are
licensed under Apache License 2.0.
"""

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QLinearGradient, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Official 24px outlined SVGs from google/material-design-icons.
_MATERIAL_OUTLINED = {
    "folder": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M9.17 6l2 2H20v10H4V6h5.17M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>'
        "</svg>"
    ),
    "file": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>'
        "</svg>"
    ),
    "help": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"/>'
        "</svg>"
    ),
    "import": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18 15v3H6v-3H4v3c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-3h-2zM7 9l1.41 1.41L11 7.83V16h2V7.83l2.59 2.58L17 9l-5-5z"/></svg>',
    "clean": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M15 16h4v2h-4zm0-8h7v2h-7zm0 4h6v2h-6zM3 18c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2V8H3v10zm2-8h6v8H5v-8zm5-6H6L5 5H2v2h12V5h-3z"/></svg>',
    "clear": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM8 9h8v10H8V9zm7.5-5-1-1h-5l-1 1H5v2h14V4z"/></svg>',
    "history": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8z"/></svg>',
    "network": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 11c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 2c0-3.31-2.69-6-6-6s-6 2.69-6 6c0 2.22 1.21 4.15 3 5.19l1-1.74c-1.19-.7-2-1.97-2-3.45 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.48-.81 2.75-2 3.45l1 1.74c1.79-1.04 3-2.97 3-5.19zM12 3C6.48 3 2 7.48 2 13c0 3.7 2.01 6.92 4.99 8.65l1-1.73C5.61 18.53 4 15.96 4 13c0-4.42 3.58-8 8-8s8 3.58 8 8c0 2.96-1.61 5.53-4 6.92l1 1.73c2.99-1.73 5-4.95 5-8.65 0-5.52-4.48-10-10-10z"/></svg>',
    "download": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18 15v3H6v-3H4v3c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-3h-2zM17 11l-1.41-1.41L13 12.17V4h-2v8.17L8.41 9.59 7 11l5 5z"/></svg>',
    "pause": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>',
    "resume": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M10 8.64 15.27 12 10 15.36V8.64M8 5v14l11-7L8 5z"/></svg>',
    "skip": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zm2-8.14L11.03 12 8 14.14V9.86zM16 6h2v12h-2z"/></svg>',
    "cancel": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/></svg>',
    "audio": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 3l.01 10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4.01 4S14 19.21 14 17V7h4V3h-6zm-1.99 16c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>',
    "video": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M4 6.47L5.76 10H20v8H4V6.47M22 4h-4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4z"/></svg>',
    "paste": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 2h-4.18C14.4.84 13.3 0 12 0S9.6.84 9.18 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z"/></svg>',
    "link": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>',
    "launch": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>',
    "chevron":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z"/></svg>',
    "minimize": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M19 13H5v-2h14v2z"/>'
        "</svg>"
    ),
    "close": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>'
        "</svg>"
    ),
}

def icon_pixmap(name: str, size: int, color: str, *, scale: float = 2.0) -> QPixmap:
    """Render one Material glyph at ``size`` logical pixels in ``color``."""
    template = _MATERIAL_OUTLINED.get(name)
    if template is None:
        raise ValueError(f"Unknown icon: {name}")

    svg = template.replace("<path d=", f'<path fill="{color}" d=', 1)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    pixels = round(size * scale)
    pixmap = QPixmap(pixels, pixels)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)

    inset = size / 24.0
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(inset, inset, size - 2 * inset, size - 2 * inset))
    painter.end()
    return pixmap


def _render_icon(name: str, color: str) -> QPixmap:
    return icon_pixmap(name, 24, color)


def brand_pixmap(size: int = 28) -> QPixmap:
    """YTDLE mark in the active skin: gradient tile, tonal tile, or the bare glyph."""
    from ui.skins import COLORS, active_skin

    style = active_skin().brand_style
    scale = 2.0
    pixmap = QPixmap(round(size * scale), round(size * scale))
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    if style == "mono":
        glyph_color = COLORS["strong"]
        glyph = size * 0.86
    else:
        if style == "tonal":
            painter.setBrush(QColor(COLORS["primary_container"]))
            glyph_color = COLORS["on_selected"]
            radius = size * 0.28
        else:
            gradient = QLinearGradient(0.0, 0.0, float(size), float(size))
            gradient.setColorAt(0.0, QColor(COLORS["accent"]))
            gradient.setColorAt(1.0, QColor("#b06cf8"))
            painter.setBrush(gradient)
            glyph_color = "#ffffff"
            radius = size * 0.3
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0.0, 0.0, size, size), radius, radius)
        glyph = size * 0.64
    offset = (size - glyph) / 2.0
    painter.drawPixmap(
        QRectF(offset, offset, glyph, glyph).toRect(),
        icon_pixmap("download", round(glyph), glyph_color),
    )
    painter.end()
    return pixmap


# Ordered 4x4 Bayer matrix: a fixed, reproducible threshold pattern.
_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def dither_pixmap(name: str, width: int, height: int, ink: str, *, cell: int = 2) -> QPixmap:
    """Ambient art: one glyph quantized once with ordered dithering.

    The tone map is the glyph's own coverage with a soft vertical and radial
    fade baked in before quantizing, so the edge dissolves into the ground.
    Marks are ``cell`` x ``cell`` squares in ``ink`` on a transparent field.
    """
    import math

    grid_w, grid_h = width // cell, height // cell
    source = QImage(grid_w, grid_h, QImage.Format.Format_ARGB32)
    source.fill(Qt.GlobalColor.transparent)
    side = min(grid_w, grid_h)
    painter = QPainter(source)
    renderer = QSvgRenderer(QByteArray(_MATERIAL_OUTLINED[name].replace(
        "<path d=", '<path fill="#ffffff" d=', 1).encode("utf-8")))
    renderer.render(painter, QRectF((grid_w - side) / 2.0, (grid_h - side) / 2.0, side, side))
    painter.end()

    pixmap = QPixmap(grid_w * cell, grid_h * cell)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    ink_color = QColor(ink)
    cx, cy = grid_w / 2.0, grid_h / 2.0
    radius = math.hypot(cx, cy)
    for y in range(grid_h):
        for x in range(grid_w):
            coverage = source.pixelColor(x, y).alphaF()
            # A faint field around the glyph keeps the mark from reading as a sticker.
            fade = max(0.0, 1.0 - math.hypot(x - cx, y - cy) / radius)
            tone = max(coverage * (0.35 + 0.65 * fade), 0.22 * fade * fade)
            threshold = (_BAYER[y % 4][x % 4] + 0.5) / 16.0
            if tone > threshold:
                painter.fillRect(x * cell, y * cell, cell, cell, ink_color)
    painter.end()
    return pixmap


def icon_action(button, name: str, label: str, *, primary: bool = False) -> None:
    """Keep a compact icon-only action usable by keyboard and assistive tools."""
    button.setText("")
    button.setIcon(line_icon(name))
    button.setIconSize(QSize(22 if primary else 20, 22 if primary else 20))
    button.setAccessibleName(label)
    if not button.toolTip():
        button.setToolTip(label)
    if not primary:
        button.setProperty("iconAction", True)
    button.setCursor(Qt.CursorShape.PointingHandCursor)


def line_icon(name: str) -> QIcon:
    """Return a DPI-aware Material outlined icon in the active skin's icon inks."""
    from ui.skins import COLORS

    icon = QIcon()
    icon.addPixmap(_render_icon(name, COLORS["icon"]), QIcon.Mode.Normal)
    icon.addPixmap(_render_icon(name, COLORS["icon_active"]), QIcon.Mode.Active)
    icon.addPixmap(_render_icon(name, COLORS["icon_disabled"]), QIcon.Mode.Disabled)
    return icon
