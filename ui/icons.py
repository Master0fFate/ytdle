"""Google Material Icons Outlined glyphs for the Angelcore desktop chrome.

Material Icons (https://github.com/google/material-design-icons) are
licensed under Apache License 2.0.
"""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Official 24px outlined SVGs from google/material-design-icons.
_MATERIAL_OUTLINED = {
    "folder": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M9.17 6l2 2H20v10H4V6h5.17M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>'
        "</svg>"
    ),
    "open-folder": (
        '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">'
        '<path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/>'
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

_STATE_COLORS = {
    QIcon.Mode.Normal: "#909090",
    QIcon.Mode.Active: "#eeeeee",
    QIcon.Mode.Disabled: "#737373",
}


def _render_icon(name: str, color: str) -> QPixmap:
    template = _MATERIAL_OUTLINED.get(name)
    if template is None:
        raise ValueError(f"Unknown icon: {name}")

    svg = template.replace("<path d=", f'<path fill="{color}" d=', 1)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(1.0, 1.0, 16.0, 16.0))
    painter.end()
    return pixmap


def line_icon(name: str) -> QIcon:
    """Return a DPI-aware Material outlined icon with hover and disabled states."""
    icon = QIcon()
    icon.addPixmap(_render_icon(name, _STATE_COLORS[QIcon.Mode.Normal]), QIcon.Mode.Normal)
    icon.addPixmap(_render_icon(name, _STATE_COLORS[QIcon.Mode.Active]), QIcon.Mode.Active)
    icon.addPixmap(_render_icon(name, _STATE_COLORS[QIcon.Mode.Disabled]), QIcon.Mode.Disabled)
    return icon
