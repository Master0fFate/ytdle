"""Small monochrome line icons that match the restrained desktop component system."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _render_icon(name: str, color: str) -> QPixmap:
    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name in {"folder", "open-folder"}:
        folder = QPainterPath(QPointF(2.0, 5.0))
        folder.lineTo(6.6, 5.0)
        folder.lineTo(8.2, 7.0)
        folder.lineTo(16.0, 7.0)
        folder.lineTo(16.0, 15.0)
        folder.lineTo(2.0, 15.0)
        folder.closeSubpath()
        painter.drawPath(folder)
        if name == "open-folder":
            painter.drawLine(QPointF(9.5, 12.5), QPointF(15.0, 7.0))
            painter.drawLine(QPointF(11.7, 7.0), QPointF(15.0, 7.0))
            painter.drawLine(QPointF(15.0, 7.0), QPointF(15.0, 10.3))
    elif name == "file":
        painter.drawRoundedRect(QRectF(4.0, 2.0, 10.0, 14.0), 1.5, 1.5)
        painter.drawLine(QPointF(9.5, 2.0), QPointF(14.0, 6.5))
        painter.drawLine(QPointF(9.5, 2.0), QPointF(9.5, 6.5))
        painter.drawLine(QPointF(9.5, 6.5), QPointF(14.0, 6.5))
    else:
        painter.end()
        raise ValueError(f"Unknown icon: {name}")

    painter.end()
    return pixmap


def line_icon(name: str) -> QIcon:
    """Return a DPI-aware monochrome icon with hover and disabled states."""
    icon = QIcon()
    icon.addPixmap(_render_icon(name, "#a1a1aa"), QIcon.Mode.Normal)
    icon.addPixmap(_render_icon(name, "#fafafa"), QIcon.Mode.Active)
    icon.addPixmap(_render_icon(name, "#52525b"), QIcon.Mode.Disabled)
    return icon
