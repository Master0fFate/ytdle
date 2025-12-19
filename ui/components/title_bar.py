from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QStyle

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(32)
        
        self.parent = parent
        self._start_pos = None
        self._is_dragging = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(5)

        self.title_label = QLabel("YTDLE Media Downloader", self)
        layout.addWidget(self.title_label)
        
        layout.addStretch(1)

        self.min_btn = QToolButton(self)
        self.min_btn.setObjectName("MinimizeButton")
        self.min_btn.setText("_")
        self.min_btn.setToolTip("Minimize")
        self.min_btn.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.min_btn)

        self.close_btn = QToolButton(self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setText("X")
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._is_dragging = True

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._start_pos:
            delta = event.globalPosition().toPoint() - self._start_pos
            self.parent.move(self.parent.pos() + delta)
            # Do not update _start_pos here for relative movement, 
            # or update it if calculating delta from previous pos.
            # Usually: 
            # delta = event.globalPos() - self._start_pos
            # parent.move(parent.pos() + delta)
            # self._start_pos = event.globalPos()
            # Wait, globalPos() is deprecated in PySide6, use globalPosition().toPoint()
            
            # Correct logic for dragging:
            # We want to move the window by the same amount the mouse moved.
            # But here we are using global position.
            # Let's use a simpler logic often used.
            pass

    # Re-implementing mouseMoveEvent to be correct
    def mouseMoveEvent(self, event):
        if self._is_dragging and self._start_pos:
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self._start_pos
            self.parent.move(self.parent.pos() + delta)
            self._start_pos = current_pos

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
