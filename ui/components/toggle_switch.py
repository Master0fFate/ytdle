from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox

from ui.skins import COLORS, active_skin


class ToggleSwitch(QCheckBox):
    """Keyboard-accessible switch drawn in the active skin's style.

    switch: a rounded track and knob. material: the Material 3 switch, whose
    knob grows when on. marks: a text mark, ``[x]`` on and ``[ ]`` off.
    """

    TRACK_WIDTH = 40.0
    TRACK_HEIGHT = 24.0
    HANDLE_SIZE = 16.0
    TEXT_GAP = 8

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._handle_position = 1.0 if self.isChecked() else 0.0
        self._hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._handle_animation = QPropertyAnimation(self, b"handlePosition", self)
        self._handle_animation.setDuration(140)
        self._handle_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate_checked_position)

    def _get_handle_position(self) -> float:
        return self._handle_position

    def _set_handle_position(self, position: float) -> None:
        self._handle_position = position
        self.update()

    handlePosition = Property(
        float,
        _get_handle_position,
        _set_handle_position,
    )

    def _animate_checked_position(self, checked: bool) -> None:
        self._handle_animation.stop()
        self._handle_animation.setStartValue(self._handle_position)
        self._handle_animation.setEndValue(1.0 if checked else 0.0)
        self._handle_animation.start()

    def showEvent(self, event) -> None:
        self._handle_animation.stop()
        self._set_handle_position(1.0 if self.isChecked() else 0.0)
        super().showEvent(event)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def _track_size(self) -> tuple[float, float]:
        if active_skin().toggle_style == "material":
            return 52.0, 32.0
        return self.TRACK_WIDTH, self.TRACK_HEIGHT

    def _mark_width(self) -> int:
        return self.fontMetrics().horizontalAdvance("[x]")

    def sizeHint(self) -> QSize:
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        if active_skin().toggle_style == "marks":
            lead = self._mark_width()
        else:
            lead = int(self._track_size()[0])
        width = lead + self.TEXT_GAP + text_width + 4
        return QSize(width, max(32, self.fontMetrics().height() + 8))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        style = active_skin().toggle_style
        if style == "marks":
            lead = self._paint_marks(painter)
        else:
            lead = self._paint_track(painter, material=style == "material")

        enabled = self.isEnabled()
        painter.setPen(QColor(COLORS["text"] if enabled else COLORS["muted"]))
        text_rect = QRectF(lead + self.TEXT_GAP, 0.0, max(0.0, self.width() - lead - self.TEXT_GAP), float(self.height()))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())

    def _paint_marks(self, painter: QPainter) -> float:
        mark = "[x]" if self.isChecked() else "[ ]"
        width = float(self._mark_width())
        if self._hovered and self.isEnabled():
            painter.fillRect(self.rect(), QColor(COLORS["selected"]))
        if self.hasFocus():
            painter.setPen(QPen(QColor(COLORS["focus"]), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0))
        if not self.isEnabled():
            color = COLORS["icon_disabled"]
        else:
            color = COLORS["strong"] if self.isChecked() else COLORS["muted"]
        painter.setPen(QColor(color))
        painter.drawText(QRectF(2.0, 0.0, width, float(self.height())), Qt.AlignmentFlag.AlignVCenter, mark)
        return width + 2.0

    def _paint_track(self, painter: QPainter, *, material: bool) -> float:
        track_w, track_h = self._track_size()
        track_y = (self.height() - track_h) / 2.0
        track = QRectF(1.0, track_y, track_w, track_h)
        enabled, checked = self.isEnabled(), self.isChecked()

        if material:
            # M3: on = primary track, larger on-primary knob; off = outlined track.
            if checked:
                track_color = QColor(COLORS["accent"] if enabled else COLORS["rule"])
                border_color = track_color
                handle_color = QColor(COLORS["on_accent"] if enabled else COLORS["bg"])
            else:
                track_color = QColor(COLORS["field"] if enabled else COLORS["surface"])
                border_color = QColor(COLORS["outline"] if enabled else COLORS["rule"])
                handle_color = QColor(COLORS["outline"] if enabled else COLORS["rule"])
            painter.setPen(QPen(border_color, 2.0))
            painter.setBrush(track_color)
            painter.drawRoundedRect(track.adjusted(1.0, 1.0, -1.0, -1.0), track_h / 2.0, track_h / 2.0)
            size = 16.0 + 8.0 * self._handle_position
            if self._hovered and enabled:
                size += 2.0
            start, end = track.left() + track_h / 2.0, track.right() - track_h / 2.0
            center_x = start + (end - start) * self._handle_position
            handle = QRectF(center_x - size / 2.0, track.center().y() - size / 2.0, size, size)
        else:
            if not enabled:
                # Checked stays recognizable while disabled: a dimmed accent track.
                track_color = QColor(COLORS["primary_container"] if checked else COLORS["surface"])
                border_color = QColor(COLORS["primary_container"] if checked else COLORS["rule"])
                handle_color = QColor(COLORS["muted"])
            elif checked:
                track_color = QColor(COLORS["accent"])
                border_color = QColor(COLORS["accent"])
                handle_color = QColor(COLORS["strong"])
            else:
                track_color = QColor(COLORS["raised"] if self._hovered else COLORS["container"])
                border_color = QColor(COLORS["outline"])
                handle_color = QColor(COLORS["text"])
            painter.setPen(QPen(border_color, 1.0))
            painter.setBrush(track_color)
            painter.drawRoundedRect(track, track_h / 2.0, track_h / 2.0)
            travel = track_w - self.HANDLE_SIZE - 8.0
            handle_x = track.left() + 4.0 + travel * self._handle_position
            handle = QRectF(handle_x, track_y + 4.0, self.HANDLE_SIZE, self.HANDLE_SIZE)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        painter.drawEllipse(handle)

        if self.hasFocus():
            painter.setPen(QPen(QColor(COLORS["focus"]), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(track.adjusted(-2.0, -2.0, 2.0, 2.0), track_h / 2.0 + 2.0, track_h / 2.0 + 2.0)
        return track.right()
