"""YTDLE Angelcore desktop visual system.

THESIS: A hard-edged downloader workspace, not a tinted dashboard.
OWN-WORLD: Near-black field, square geometry, mono type, sparse royal purple.
STORY: Read readiness, configure the job, then act without visual noise.
FIRST VIEWPORT: One dense operational canvas with a single purple primary action.
FORM: Existing Download / Cookies workflow; native desktop behavior stays visible.

Purple (#7c3aed) is a documented exception to reference-monochrome: primary
action, focus, selected tab, progress chunk, and checked switch only.
"""

COLORS = {
    "bg": "#090909",
    "surface": "#111111",
    "selected": "#191919",
    "rule": "#2b2b2b",
    "edge": "#3a3a3a",
    "control": "#737373",
    "muted": "#909090",
    "text": "#b8b8b8",
    "strong": "#eeeeee",
    "accent": "#7c3aed",
    "accent_hover": "#6d28d9",
    "accent_pressed": "#5b21b6",
    "focus": "#7c3aed",
    "field": "#090909",
}

_MONO = '"Consolas", "Cascadia Mono", "Courier New", monospace'

STYLESHEET = f"""
QMainWindow#MainWindow {{
    background-color: {COLORS["bg"]};
    border: 1px solid {COLORS["rule"]};
    border-radius: 0;
    color: {COLORS["text"]};
    font-family: {_MONO};
    font-size: 9pt;
}}
QDialog, QMessageBox {{
    background-color: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: {_MONO};
    font-size: 9pt;
    border-radius: 0;
}}
QWidget {{ color: {COLORS["text"]}; }}
QLabel {{ color: {COLORS["text"]}; }}
QLabel:disabled {{ color: {COLORS["muted"]}; }}
QToolTip {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["edge"]};
    border-radius: 0;
    padding: 6px 8px;
    font-family: {_MONO};
}}
QMenu {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["edge"]};
    border-radius: 0;
    color: {COLORS["text"]};
    padding: 4px;
}}
QMenu::item {{
    background-color: transparent;
    color: {COLORS["text"]};
    border-radius: 0;
    padding: 5px 28px 5px 28px;
}}
QMenu::item:selected {{
    background-color: {COLORS["selected"]};
    color: {COLORS["strong"]};
}}
QMenu::item:disabled {{ color: {COLORS["muted"]}; }}
QMenu::separator {{
    height: 1px;
    background-color: {COLORS["rule"]};
    margin: 4px 8px;
}}

#TitleBar {{
    background-color: {COLORS["surface"]};
    border-bottom: 1px solid {COLORS["rule"]};
    border-radius: 0;
}}
#TitleBar QLabel#WindowTitle {{
    color: {COLORS["strong"]};
    font-size: 10pt;
    font-weight: 600;
}}
QToolButton#MinimizeButton, QToolButton#CloseButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 0;
    color: {COLORS["muted"]};
    min-width: 28px;
    min-height: 26px;
    padding: 0;
}}
QToolButton#MinimizeButton:hover, QToolButton#CloseButton:hover {{
    background-color: {COLORS["selected"]};
    color: {COLORS["strong"]};
}}
QToolButton#MinimizeButton:pressed, QToolButton#CloseButton:pressed {{
    background-color: {COLORS["bg"]};
}}
QToolButton#MinimizeButton:focus, QToolButton#CloseButton:focus {{
    border: 1px solid transparent;
    background-color: {COLORS["selected"]};
}}

QFrame {{ border: none; }}
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background-color: {COLORS["field"]};
    border: none;
    border-bottom: 1px solid {COLORS["rule"]};
    border-radius: 0;
    color: {COLORS["strong"]};
    selection-background-color: {COLORS["selected"]};
    selection-color: {COLORS["strong"]};
    font-family: {_MONO};
}}
QLineEdit, QComboBox {{
    min-height: 22px;
    padding: 3px 8px;
}}
QLineEdit::placeholder, QPlainTextEdit::placeholder {{ color: {COLORS["muted"]}; }}
QPlainTextEdit {{ padding: 8px 10px; }}
QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextBrowser:hover {{
    border: none;
    border-bottom: 1px solid {COLORS["edge"]};
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    background-color: {COLORS["field"]};
    border: none;
    border-bottom: 1px solid {COLORS["focus"]};
}}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    background-color: {COLORS["bg"]};
    border: none;
    border-bottom: 1px solid {COLORS["rule"]};
    color: {COLORS["muted"]};
}}

QComboBox {{ padding-right: 22px; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 18px;
    border: none;
    border-radius: 0;
}}
QComboBox::down-arrow {{ width: 8px; height: 8px; }}
QComboBox QAbstractItemView {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["edge"]};
    border-radius: 0;
    outline: 0;
    selection-background-color: {COLORS["selected"]};
    selection-color: {COLORS["strong"]};
    padding: 4px;
}}

QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: {COLORS["text"]};
    min-height: 22px;
    padding: 3px 9px;
    font-family: {_MONO};
}}
QPushButton:hover {{
    background-color: {COLORS["selected"]};
    color: {COLORS["strong"]};
}}
QPushButton:pressed {{ background-color: {COLORS["bg"]}; }}
QPushButton:focus, QToolButton:focus {{
    border: none;
    border-bottom: 1px solid {COLORS["focus"]};
}}
QPushButton:disabled {{
    background-color: transparent;
    color: {COLORS["muted"]};
}}
QFrame#FormatSwitch {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {COLORS["rule"]};
    border-radius: 0;
}}
QFrame#FormatSwitch QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    min-width: 46px;
    min-height: 22px;
    padding: 3px 10px;
}}
QFrame#FormatSwitch QPushButton:hover {{ background-color: {COLORS["selected"]}; }}
QFrame#FormatSwitch QPushButton:checked {{
    background-color: {COLORS["selected"]};
    color: {COLORS["strong"]};
}}
QFrame#FormatSwitch QPushButton#FormatSegmentLeft {{
    border-radius: 0;
    border-right: 1px solid {COLORS["rule"]};
}}
QFrame#FormatSwitch QPushButton#FormatSegmentRight {{
    border-radius: 0;
}}
QFrame#FormatSwitch QPushButton:focus {{
    border: none;
    border-bottom: 1px solid {COLORS["focus"]};
}}
QPushButton#DownloadButton {{
    background-color: {COLORS["accent"]};
    border: none;
    color: {COLORS["strong"]};
    font-weight: 600;
    min-height: 24px;
    padding: 4px 12px;
}}
QPushButton#DownloadButton:hover {{
    background-color: {COLORS["accent_hover"]};
    border: none;
}}
QPushButton#DownloadButton:pressed {{
    background-color: {COLORS["accent_pressed"]};
    border: none;
}}
QPushButton#DownloadButton:disabled {{
    background-color: {COLORS["surface"]};
    border: none;
    color: {COLORS["muted"]};
}}
QPushButton#DownloadButton:focus {{
    border: none;
}}
QPushButton#CancelButton, QPushButton#PauseButton, QPushButton#SkipButton {{
    min-height: 24px;
    padding: 4px 9px;
}}

QToolButton#BrowseButton, QToolButton#OpenFolderButton, QToolButton#CookieBrowseButton {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: {COLORS["text"]};
    min-width: 26px;
    min-height: 26px;
    padding: 2px;
}}
QToolButton#BrowseButton:hover, QToolButton#OpenFolderButton:hover, QToolButton#CookieBrowseButton:hover {{
    background-color: {COLORS["selected"]};
}}

QCheckBox {{
    color: {COLORS["muted"]};
    spacing: 6px;
    padding: 2px 1px;
}}
QCheckBox:hover, QCheckBox:focus {{ color: {COLORS["strong"]}; }}
QCheckBox:disabled {{ color: {COLORS["muted"]}; }}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {COLORS["edge"]};
    border-radius: 0;
    background: {COLORS["field"]};
}}
QCheckBox::indicator:checked {{
    background: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}
ToggleSwitch {{ background-color: transparent; padding: 0; }}

QProgressBar {{
    background-color: {COLORS["surface"]};
    border: none;
    border-radius: 0;
    color: {COLORS["muted"]};
    min-height: 16px;
    text-align: center;
    font-family: {_MONO};
}}
QProgressBar::chunk {{ background-color: {COLORS["accent"]}; border-radius: 0; }}

QLabel#DependencyStatus, QLabel#NetworkLabel, QLabel#StatusLabel {{
    color: {COLORS["muted"]};
    background-color: transparent;
    border: none;
    border-radius: 0;
    padding: 4px 8px;
}}
QLabel#DependencyStatus {{ min-height: 22px; }}
QLabel#StatusLabel {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    padding: 2px 2px;
}}
QLabel#DependencyStatus[state="ready"], QLabel#NetworkLabel[state="ready"], QLabel#StatusLabel[state="ready"] {{
    color: {COLORS["text"]};
}}
QLabel#DependencyStatus[state="partial"], QLabel#NetworkLabel[state="warning"], QLabel#StatusLabel[state="warning"] {{
    color: {COLORS["strong"]};
    border-color: {COLORS["rule"]};
}}
QLabel#DependencyStatus[state="warning"], QLabel#NetworkLabel[state="error"], QLabel#StatusLabel[state="error"] {{
    color: {COLORS["strong"]};
    border-color: {COLORS["rule"]};
}}
QLabel#StatusLabel[state="active"] {{ color: {COLORS["strong"]}; }}
QLabel#QueueSummary {{
    color: {COLORS["muted"]};
    background-color: transparent;
    border: none;
    border-radius: 0;
    padding: 2px 4px;
}}
QLabel#QueueSummary[state="notice"] {{ color: {COLORS["strong"]}; }}
QLabel#QueueSummary[state="warning"] {{ color: {COLORS["strong"]}; }}
QPushButton#ImportUrlsButton, QPushButton#CleanUrlsButton, QPushButton#ClearUrlsButton, QPushButton#CheckNetworkButton {{
    min-height: 22px;
    padding: 3px 8px;
}}
QPlainTextEdit#LogOutput {{
    background-color: {COLORS["bg"]};
    border: none;
    border-top: 1px solid {COLORS["rule"]};
    color: {COLORS["text"]};
    font-family: {_MONO};
    font-size: 8.5pt;
    border-radius: 0;
}}
QPlainTextEdit#LogOutput:focus {{
    border: none;
    border-top: 1px solid {COLORS["rule"]};
}}

QTabWidget::pane {{
    background-color: {COLORS["bg"]};
    border: none;
    border-top: 1px solid {COLORS["rule"]};
    border-radius: 0;
    top: -1px;
}}
QTabBar::tab {{
    background-color: transparent;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    color: {COLORS["muted"]};
    font-weight: 500;
    min-height: 24px;
    padding: 4px 12px;
    margin-right: 2px;
}}
QTabBar::tab:hover {{ color: {COLORS["strong"]}; background-color: {COLORS["selected"]}; }}
QTabBar::tab:selected {{
    color: {COLORS["strong"]};
    background-color: transparent;
    border-bottom-color: {COLORS["accent"]};
}}
QTabBar::tab:focus {{ border: none; border-bottom: 2px solid {COLORS["focus"]}; }}

QGroupBox {{
    background-color: {COLORS["bg"]};
    border: none;
    border-top: 1px solid {COLORS["rule"]};
    border-radius: 0;
    color: {COLORS["text"]};
    font-weight: 600;
    margin-top: 12px;
    padding: 8px 8px 6px 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 9px;
    padding: 0 6px;
    color: {COLORS["strong"]};
    background-color: {COLORS["bg"]};
}}
QToolButton#HelpButton {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: {COLORS["text"]};
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
    padding: 2px;
}}
QToolButton#HelpButton:hover {{
    background-color: {COLORS["selected"]};
}}
QLabel#CookieTip {{ color: {COLORS["muted"]}; font-size: 9pt; }}

QDialog#HistoryDialog, QDialog#HelpDialog {{ background-color: {COLORS["bg"]}; border-radius: 0; }}
QLabel#DialogTitle {{ color: {COLORS["strong"]}; font-size: 13pt; font-weight: 600; }}
QTableWidget {{
    background-color: {COLORS["surface"]};
    alternate-background-color: {COLORS["bg"]};
    border: none;
    border-top: 1px solid {COLORS["rule"]};
    border-radius: 0;
    color: {COLORS["text"]};
    gridline-color: {COLORS["rule"]};
    selection-background-color: {COLORS["selected"]};
    selection-color: {COLORS["strong"]};
}}
QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {COLORS["rule"]}; }}
QTableWidget::item:selected {{ background-color: {COLORS["selected"]}; color: {COLORS["strong"]}; }}
QTableWidget QHeaderView::section {{
    background-color: {COLORS["surface"]};
    border: none;
    border-bottom: 1px solid {COLORS["rule"]};
    border-right: 1px solid {COLORS["rule"]};
    border-radius: 0;
    color: {COLORS["strong"]};
    font-weight: 600;
    padding: 7px;
}}
QTextBrowser {{ padding: 10px; }}
QScrollBar:vertical {{ background: {COLORS["bg"]}; width: 10px; margin: 2px; border-radius: 0; }}
QScrollBar::handle:vertical {{
    background: {COLORS["edge"]};
    min-height: 24px;
    border-radius: 0;
}}
QScrollBar::handle:vertical:hover {{ background: {COLORS["muted"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def strip_native_frames(root) -> None:
    """Disable Qt's sunken frames so Windows cannot paint white bevels."""
    from PySide6.QtWidgets import QFrame, QGroupBox, QLineEdit, QPlainTextEdit, QTextBrowser

    for widget in root.findChildren(QLineEdit):
        widget.setFrame(False)
    for widget in root.findChildren(QPlainTextEdit):
        widget.setFrameStyle(QFrame.Shape.NoFrame)
    for widget in root.findChildren(QTextBrowser):
        widget.setFrameStyle(QFrame.Shape.NoFrame)
    for widget in root.findChildren(QGroupBox):
        widget.setFlat(True)


def apply_chrome(app) -> None:
    """Kill native Windows light bevels, then apply the Angelcore stylesheet."""
    from PySide6.QtGui import QColor, QPalette

    app.setStyle("Fusion")
    palette = app.palette()
    ink = {
        QPalette.ColorRole.Window: COLORS["bg"],
        QPalette.ColorRole.Base: COLORS["field"],
        QPalette.ColorRole.AlternateBase: COLORS["surface"],
        QPalette.ColorRole.Button: COLORS["surface"],
        QPalette.ColorRole.ButtonText: COLORS["text"],
        QPalette.ColorRole.WindowText: COLORS["text"],
        QPalette.ColorRole.Text: COLORS["text"],
        QPalette.ColorRole.PlaceholderText: COLORS["muted"],
        QPalette.ColorRole.BrightText: COLORS["strong"],
        QPalette.ColorRole.Light: COLORS["bg"],
        QPalette.ColorRole.Midlight: COLORS["bg"],
        QPalette.ColorRole.Mid: COLORS["rule"],
        QPalette.ColorRole.Dark: COLORS["bg"],
        QPalette.ColorRole.Shadow: COLORS["bg"],
        QPalette.ColorRole.Highlight: COLORS["accent"],
        QPalette.ColorRole.HighlightedText: COLORS["strong"],
        QPalette.ColorRole.ToolTipBase: COLORS["surface"],
        QPalette.ColorRole.ToolTipText: COLORS["text"],
    }
    for role, color in ink.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)

