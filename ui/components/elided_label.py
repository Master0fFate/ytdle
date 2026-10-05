from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy

from ui.text import plain_tip


class ElidedLabel(QLabel):
    """One-line label that shortens long text with "…" instead of widening the window.

    ``elide`` picks which part survives: ElideRight keeps the start;
    ElideMiddle keeps both ends, for lines that end in a folder name.
    """

    def __init__(self, text: str = "", parent=None, *, elide=Qt.TextElideMode.ElideRight):
        super().__init__(text, parent)
        self._elide = elide
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def paintEvent(self, _event) -> None:
        rect = self.contentsRect()
        full = self.text()
        shown = self.fontMetrics().elidedText(full, self._elide, rect.width())
        # Full text stays reachable when the visible line is shortened.
        tip = plain_tip(full) if shown != full else ""
        if self.toolTip() != tip:
            self.setToolTip(tip)
        painter = QPainter(self)
        self.style().drawItemText(
            painter,
            rect,
            int(self.alignment() | Qt.AlignmentFlag.AlignVCenter),
            self.palette(),
            self.isEnabled(),
            shown,
            self.foregroundRole(),
        )
