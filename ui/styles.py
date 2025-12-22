STYLESHEET = """
QMainWindow#MainWindow {
    background-color: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

/* Labels */
QLabel { color: #ffffff; }

/* Custom Title Bar */
#TitleBar {
    background-color: #1e1e1e;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
#TitleBar QLabel { color: #ffffff; font-weight: 600; }

/* Title bar buttons */
QToolButton#MinimizeButton, QToolButton#CloseButton {
    background-color: transparent;
    border: none;
    padding: 3px 6px;
    border-radius: 4px;
    color: #ffffff;
    min-height: 18px;
}
QToolButton#MinimizeButton:hover { background-color: #2a2a2a; }
QToolButton#CloseButton:hover { background-color: #c42b1c; }

/* Inputs (compact) */
QLineEdit, QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 4px 6px;
    color: #ffffff;
    min-height: 26px;
}
QPlainTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 6px 8px;
    color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #0a84ff; }

/* ComboBox - tighter drop-down */
QComboBox { padding-right: 24px; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #2a2a2a;
    background-color: #1e1e1e;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #2a2a2a;
    selection-background-color: #1677ff;
    selection-color: #ffffff;
}

/* Buttons (compact, fluent-like) */
QPushButton {
    background-color: #1f1f1f;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #ffffff;
    min-height: 26px;
}
QPushButton:hover { background-color: #2a2a2a; }
QPushButton:pressed { background-color: #343434; }

/* Format toggles (MP3/MP4) */
QPushButton[formatToggle="true"] { background-color: #1f1f1f; border: 1px solid #2a2a2a; }
QPushButton[formatToggle="true"]:hover { background-color: #262626; border: 1px solid #333333; }
QPushButton[formatToggle="true"]:checked { background-color: #0a84ff; border: 1px solid #1677ff; color: #ffffff; }
QPushButton[formatToggle="true"]:checked:hover { background-color: #1677ff; }

/* Primary/secondary */
QPushButton#DownloadButton {
    background-color: #0a84ff;
    border: 1px solid #1677ff;
    font-weight: bold;
    min-height: 28px;
    padding: 8px 12px;
}
QPushButton#DownloadButton:hover { background-color: #1677ff; }
QPushButton#CancelButton {
    background-color: #3a3a3a;
    border: 1px solid #2a2a2a;
}

/* Tool buttons */
QToolButton#BrowseButton, QToolButton#OpenFolderButton {
    background-color: #1f1f1f;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 4px;
    color: #ffffff;
    min-height: 22px;
}
QToolButton#BrowseButton:hover, QToolButton#OpenFolderButton:hover { background-color: #262626; }

/* Progress (compact) */
QProgressBar {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    min-height: 16px;
}
QProgressBar::chunk { background-color: #0a84ff; border-radius: 4px; }

/* CheckBox Styling */
QCheckBox {
    spacing: 8px;
    color: #ffffff;
    padding: 4px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 3px;
}
QCheckBox::indicator:hover {
    border: 1px solid #0a84ff;
    background-color: #2a2a2a;
}
QCheckBox::indicator:checked {
    background-color: #0a84ff;
    border: 1px solid #0a84ff;
}

/* History Button */
QPushButton#HistoryButton {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    min-height: 28px;
    padding: 8px 12px;
}
QPushButton#HistoryButton:hover { background-color: #3a3a3a; }

/* Network Label */
QLabel#NetworkLabel {
    color: #aaaaaa;
    padding: 4px 8px;
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    min-height: 22px;
}

/* Check Network Button */
QPushButton#CheckNetworkButton {
    background-color: #1f1f1f;
    border: 1px solid #2a2a2a;
    min-height: 22px;
    padding: 4px 8px;
}
QPushButton#CheckNetworkButton:hover { background-color: #2a2a2a; }

/* Pause Button */
QPushButton#PauseButton {
    background-color: #3a3a3a;
    border: 1px solid #2a2a2a;
    min-height: 28px;
    padding: 8px 12px;
}
QPushButton#PauseButton:hover { background-color: #4a4a4a; }

/* Skip Button */
QPushButton#SkipButton {
    background-color: #3a3a3a;
    border: 1px solid #2a2a2a;
    min-height: 28px;
    padding: 8px 12px;
}
QPushButton#SkipButton:hover { background-color: #4a4a4a; }

/* History Dialog */
QDialog#HistoryDialog {
    background-color: #121212;
    color: #ffffff;
}
QDialog#HistoryDialog QLabel {
    color: #ffffff;
}

/* History Dialog Table */
QTableWidget {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    color: #ffffff;
    selection-background-color: #1677ff;
    selection-color: #ffffff;
    alternate-background-color: #252525;
}
QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #2a2a2a;
}
QTableWidget::item:selected {
    background-color: #1677ff;
    color: #ffffff;
}
QTableWidget QHeaderView::section {
    background-color: #1f1f1f;
    color: #ffffff;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #2a2a2a;
    border-right: 1px solid #2a2a2a;
}

/* History Dialog Tabs */
QTabWidget::pane {
    border: 1px solid #2a2a2a;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #1f1f1f;
    color: #aaaaaa;
    padding: 6px 12px;
    border: 1px solid #2a2a2a;
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
}
QTabBar::tab:hover {
    background-color: #252525;
}
"""
