from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from ui.icons import line_icon


class CustomTitleBar(QWidget):
    """Minimal frameless-window title bar with native drag behavior."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        self.parent = parent
        self._start_pos = None
        self._is_dragging = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(4)

        self.title_label = QLabel("YTDLE Media Downloader", self)
        self.title_label.setObjectName("WindowTitle")
        self.title_label.setAccessibleName("YTDLE Media Downloader")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.min_btn = QToolButton(self)
        self.min_btn.setObjectName("MinimizeButton")
        self.min_btn.setIcon(line_icon("minimize"))
        self.min_btn.setIconSize(QSize(16, 16))
        self.min_btn.setToolTip("Minimize")
        self.min_btn.setAccessibleName("Minimize window")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = QToolButton(self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setIcon(line_icon("close"))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setToolTip("Close")
        self.close_btn.setAccessibleName("Close window")
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._is_dragging = True

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._start_pos:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._start_pos
            self.parent.move(self.parent.pos() + delta)
            self._start_pos = current_pos

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
