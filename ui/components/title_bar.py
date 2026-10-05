from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from ui.icons import brand_pixmap, line_icon


class CustomTitleBar(QWidget):
    """Frameless-window title bar: brand, page slots, and window buttons.

    Dragging uses the platform's system move, so Windows snap layouts work.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        # Lets skins draw a background or a rule on this plain QWidget.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # The styled window buttons are 38 px tall; keep their full hit targets
        # inside the draggable title surface rather than clipping the top edge.
        self.setFixedHeight(52)
        self.parent = parent
        self._start_pos = None
        self._is_dragging = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(8)

        self.brand_icon = QLabel(self)
        self.brand_icon.setPixmap(brand_pixmap(28))
        self.brand_icon.setFixedSize(28, 28)
        layout.addWidget(self.brand_icon)

        self.title_label = QLabel("YTDLE", self)
        self.title_label.setObjectName("BrandName")
        self.title_label.setAccessibleName("YTDLE Media Downloader")
        layout.addWidget(self.title_label)
        layout.addSpacing(10)

        self.leading = QHBoxLayout()
        self.leading.setSpacing(6)
        layout.addLayout(self.leading)
        layout.addStretch(1)

        self.trailing = QHBoxLayout()
        self.trailing.setSpacing(6)
        layout.addLayout(self.trailing)
        layout.addSpacing(6)

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

    def refresh_skin(self) -> None:
        """Redraw the brand mark and window glyphs in the active skin."""
        self.brand_icon.setPixmap(brand_pixmap(28))
        self.min_btn.setIcon(line_icon("minimize"))
        self.close_btn.setIcon(line_icon("close"))

    def add_leading(self, widget: QWidget) -> None:
        self.leading.addWidget(widget)

    def add_trailing(self, widget: QWidget) -> None:
        self.trailing.addWidget(widget)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        handle = self.window().windowHandle()
        if handle is not None and handle.startSystemMove():
            return
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

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        window = self.window()
        if window.isMaximized():
            window.showNormal()
        else:
            window.showMaximized()
