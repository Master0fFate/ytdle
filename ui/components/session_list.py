"""Per-link view of the current download session."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Optional
from urllib.parse import urlsplit

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
)

from ui.skins import COLORS, active_skin
from ui.text import plain_tip

STATE_ROLE = Qt.ItemDataRole.UserRole
DETAIL_ROLE = Qt.ItemDataRole.UserRole + 1
URL_ROLE = Qt.ItemDataRole.UserRole + 2

STATE_LABELS = {
    "queued": "Waiting",
    "active": "Downloading",
    "done": "Saved",
    "failed": "Failed",
    "skipped": "Skipped",
    "stopped": "Not started",
}
# Text marks for skins that show state in words instead of colored dots.
_STATE_MARKS = {
    "queued": "[ ]",
    "active": "...",
    "done": "[ok]",
    "failed": "[!]",
    "skipped": "[-]",
    "stopped": "[-]",
}


def _state_color(state: str) -> str:
    if active_skin().state_marks:
        # Neutral inks: what matters is brighter, the rest recedes.
        return COLORS["strong"] if state in ("failed", "active") else COLORS["muted"]
    return {
        "queued": COLORS["outline"],
        "active": COLORS["focus"],
        "done": COLORS["success"],
        "failed": COLORS["error"],
        "skipped": COLORS["warning"],
        "stopped": COLORS["rule"],
    }.get(state, COLORS["outline"])


def display_url(url: str) -> str:
    """Short, readable form of a link: host without www, plus path and query."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    host = (parts.hostname or "").removeprefix("www.")
    if not host:
        return url
    rest = parts.path.rstrip("/")
    if parts.query:
        rest += f"?{parts.query}"
    return host + rest


def _one_step_smaller(font: QFont) -> None:
    """Shrink by one step in whichever unit the font was set (points or pixels)."""
    if font.pointSizeF() > 0:
        font.setPointSizeF(max(7.0, font.pointSizeF() - 1.0))
    elif font.pixelSize() > 0:
        font.setPixelSize(max(10, font.pixelSize() - 1))


class _SessionDelegate(QStyledItemDelegate):
    ROW_HEIGHT = 44

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), self.ROW_HEIGHT)

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = option.rect.adjusted(0, 2, -2, -2)

        if option.state & QStyle.StateFlag.State_Selected:
            background = QColor(COLORS["raised"])
        elif option.state & QStyle.StateFlag.State_MouseOver:
            background = QColor(COLORS["container"])
        else:
            background = None
        if background is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(background)
            corner = 0.0 if active_skin().state_marks else 12.0
            painter.drawRoundedRect(QRectF(rect), corner, corner)

        state = index.data(STATE_ROLE) or "queued"
        color = QColor(_state_color(state))
        if active_skin().state_marks:
            painter.setPen(color)
            mark_rect = QRect(rect.left() + 8, rect.top(), painter.fontMetrics().horizontalAdvance("[ok]") + 2, rect.height())
            painter.drawText(mark_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, _STATE_MARKS.get(state, ""))
            text_left = mark_rect.right() + 10
        else:
            dot = QRectF(rect.left() + 12.0, rect.center().y() - 4.0, 8.0, 8.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(dot)
            text_left = int(dot.right()) + 12

        label = STATE_LABELS.get(state, state)
        label_font = QFont(option.font)
        if not active_skin().state_marks:
            label_font.setWeight(QFont.Weight.DemiBold)
        _one_step_smaller(label_font)
        painter.setFont(label_font)
        label_width = painter.fontMetrics().horizontalAdvance(label)
        label_rect = QRect(rect.right() - 12 - label_width, rect.top(), label_width, rect.height())
        painter.setPen(color)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, label)

        left = text_left
        width = max(0, label_rect.left() - 16 - left)
        title = index.data(Qt.ItemDataRole.DisplayRole) or ""
        detail = index.data(DETAIL_ROLE) or ""

        painter.setFont(option.font)
        painter.setPen(QColor(COLORS["text"]))
        metrics = painter.fontMetrics()
        title = metrics.elidedText(title, Qt.TextElideMode.ElideMiddle, width)
        if not detail:
            painter.drawText(
                QRect(left, rect.top(), width, rect.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                title,
            )
        else:
            half = rect.height() // 2
            painter.drawText(
                QRect(left, rect.top(), width, half),
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                title,
            )
            detail_font = QFont(option.font)
            _one_step_smaller(detail_font)
            painter.setFont(detail_font)
            painter.setPen(QColor(COLORS["muted"]))
            detail = painter.fontMetrics().elidedText(
                detail, Qt.TextElideMode.ElideMiddle, width
            )
            painter.drawText(
                QRect(left, rect.top() + half + 1, width, half),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                detail,
            )
        painter.restore()


class SessionList(QListWidget):
    """One row per queued link, with a colored state dot and a plain-word state."""

    PLACEHOLDER = "Links you download appear here, one row each."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SessionList")
        self.setAccessibleName("Downloads in this session")
        self.setItemDelegate(_SessionDelegate(self))
        self.setUniformItemSizes(True)
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._items: dict[str, QListWidgetItem] = {}

    def start_session(self, urls: Iterable[str]) -> None:
        self.setUpdatesEnabled(False)
        try:
            self.clear()
            self._items = {}
            for url in urls:
                item = QListWidgetItem(display_url(url))
                item.setData(STATE_ROLE, "queued")
                item.setData(URL_ROLE, url)
                item.setToolTip(plain_tip(url))
                self.addItem(item)
                self._items[url] = item
        finally:
            self.setUpdatesEnabled(True)

    def set_state(self, url: str, state: str, detail: str = "") -> None:
        item = self._items.get(url)
        if item is None:
            return
        item.setData(STATE_ROLE, state)
        item.setData(DETAIL_ROLE, detail)
        item.setToolTip(plain_tip(f"{url}\n{detail}" if detail else url))
        if state == "active":
            self.scrollToItem(item)

    def finish_session(self) -> None:
        """Items that never reached a final state did not start; say so."""
        for item in self._items.values():
            if item.data(STATE_ROLE) in ("queued", "active"):
                item.setData(STATE_ROLE, "stopped")

    def counts(self) -> Counter:
        return Counter(item.data(STATE_ROLE) for item in self._items.values())

    @staticmethod
    def item_state(item: QListWidgetItem) -> str:
        return item.data(STATE_ROLE) or ""

    @staticmethod
    def item_detail(item: QListWidgetItem) -> str:
        return item.data(DETAIL_ROLE) or ""

    @staticmethod
    def item_url(item: QListWidgetItem) -> Optional[str]:
        return item.data(URL_ROLE)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.count():
            return
        painter = QPainter(self.viewport())
        painter.setPen(QColor(COLORS["muted"]))
        painter.drawText(
            self.viewport().rect().adjusted(12, 0, -12, 0),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.PLACEHOLDER,
        )
