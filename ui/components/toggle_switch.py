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


class ToggleSwitch(QCheckBox):
    """Compact keyboard-accessible switch with one short, event-driven transition."""

    TRACK_WIDTH = 32.0
    TRACK_HEIGHT = 18.0
    HANDLE_SIZE = 14.0
    TEXT_GAP = 7

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

    def sizeHint(self) -> QSize:
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        width = int(self.TRACK_WIDTH) + self.TEXT_GAP + text_width + 2
        return QSize(width, max(22, self.fontMetrics().height() + 4))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        track_y = (self.height() - self.TRACK_HEIGHT) / 2.0
        track = QRectF(1.0, track_y, self.TRACK_WIDTH, self.TRACK_HEIGHT)
        if not self.isEnabled():
            track_color = QColor("#111111")
            border_color = QColor("#2b2b2b")
            handle_color = QColor("#737373")
            text_color = QColor("#909090")
        elif self.isChecked():
            track_color = QColor("#7c3aed")
            border_color = QColor("#7c3aed")
            handle_color = QColor("#eeeeee")
            text_color = QColor("#eeeeee")
        else:
            track_color = QColor("#191919" if self._hovered else "#111111")
            border_color = QColor("#2b2b2b")
            handle_color = QColor("#909090")
            text_color = QColor("#eeeeee" if self._hovered else "#909090")

        painter.setPen(QPen(border_color, 1.0))
        painter.setBrush(track_color)
        painter.drawRect(track)

        travel = self.TRACK_WIDTH - self.HANDLE_SIZE - 4.0
        handle_x = track.left() + 2.0 + travel * self._handle_position
        handle = QRectF(
            handle_x,
            track_y + 2.0,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(handle_color)
        painter.drawRect(handle)

        if self.hasFocus():
            painter.setPen(QPen(QColor("#7c3aed"), 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(track.adjusted(-1.0, -1.0, 1.0, 1.0))

        painter.setPen(text_color)
        text_rect = QRectF(
            track.right() + self.TEXT_GAP,
            0.0,
            max(0.0, self.width() - track.right() - self.TEXT_GAP),
            float(self.height()),
        )
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )
