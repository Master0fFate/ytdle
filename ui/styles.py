"""YTDLE's restrained, shadcn-inspired dark desktop visual system.

THESIS: A precise downloader workspace, not a tinted dashboard.
OWN-WORLD: Zinc-black surfaces, crisp hairline borders, and sparse royal purple.
STORY: Read readiness, configure the job, then act without visual noise.
FIRST VIEWPORT: One dense operational canvas with a single purple primary action.
FORM: User-pinned familiar component system; native desktop behavior stays visible.
"""

COLORS = {
    "canvas": "#09090b",
    "panel": "#0f0f12",
    "surface": "#121216",
    "surface_raised": "#18181b",
    "surface_hover": "#202024",
    "field": "#0c0c0f",
    "border": "#27272a",
    "border_strong": "#3f3f46",
    "text": "#fafafa",
    "text_muted": "#a1a1aa",
    "text_subtle": "#7c7c85",
    "text_disabled": "#5f5f68",
    "accent": "#7c3aed",
    "accent_hover": "#6d28d9",
    "accent_pressed": "#5b21b6",
    "accent_soft": "#1d162d",
    "focus": "#8b5cf6",
    "success": "#86efac",
    "warning": "#fde68a",
    "danger": "#fca5a5",
}


STYLESHEET = f"""
QMainWindow#MainWindow {{
    background-color: {COLORS["canvas"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    color: {COLORS["text"]};
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 9.5pt;
}}
QDialog, QMessageBox {{
    background-color: {COLORS["canvas"]};
    color: {COLORS["text"]};
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 9.5pt;
}}
QWidget {{ color: {COLORS["text"]}; }}
QLabel {{ color: {COLORS["text"]}; }}
QLabel:disabled {{ color: {COLORS["text_disabled"]}; }}
QToolTip {{
    background-color: {COLORS["surface_raised"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border_strong"]};
    border-radius: 5px;
    padding: 6px 8px;
}}
QMenu {{
    background-color: {COLORS["surface_raised"]};
    border: 1px solid {COLORS["border_strong"]};
    color: {COLORS["text"]};
    padding: 4px;
}}
QMenu::item {{
    background-color: transparent;
    color: {COLORS["text"]};
    border-radius: 4px;
    padding: 5px 28px 5px 28px;
}}
QMenu::item:selected {{
    background-color: {COLORS["surface_hover"]};
    color: {COLORS["text"]};
}}
QMenu::item:disabled {{ color: {COLORS["text_disabled"]}; }}
QMenu::separator {{
    height: 1px;
    background-color: {COLORS["border"]};
    margin: 4px 8px;
}}

/* Flat application chrome: no image, glow, gradient, or decorative texture. */
#TitleBar {{
    background-color: {COLORS["panel"]};
    border-bottom: 1px solid {COLORS["border"]};
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
}}
#TitleBar QLabel#WindowTitle {{
    color: {COLORS["text"]};
    font-size: 10pt;
    font-weight: 600;
}}
QToolButton#MinimizeButton, QToolButton#CloseButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    color: {COLORS["text_muted"]};
    font-size: 15px;
    font-weight: 500;
    min-width: 28px;
    min-height: 26px;
    padding: 0;
}}
QToolButton#MinimizeButton:hover, QToolButton#CloseButton:hover {{
    background-color: {COLORS["surface_hover"]};
    color: {COLORS["text"]};
}}
QToolButton#CloseButton:hover {{ color: {COLORS["danger"]}; }}
QToolButton#MinimizeButton:pressed, QToolButton#CloseButton:pressed {{
    background-color: {COLORS["surface_raised"]};
}}

QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background-color: {COLORS["field"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
}}
QLineEdit, QComboBox {{
    min-height: 22px;
    padding: 3px 8px;
}}
QLineEdit::placeholder, QPlainTextEdit::placeholder {{ color: {COLORS["text_subtle"]}; }}
QPlainTextEdit {{ padding: 8px 10px; }}
QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextBrowser:hover {{
    border-color: {COLORS["border_strong"]};
}}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    background-color: {COLORS["field"]};
    border: 1px solid {COLORS["focus"]};
}}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    background-color: {COLORS["canvas"]};
    border-color: #1f1f23;
    color: {COLORS["text_disabled"]};
}}

QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {COLORS["border"]};
}}
QComboBox::down-arrow {{ width: 9px; height: 9px; }}
QComboBox QAbstractItemView {{
    background-color: {COLORS["surface_raised"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border_strong"]};
    outline: 0;
    selection-background-color: #2e1f4f;
    selection-color: #ffffff;
    padding: 4px;
}}

QPushButton {{
    background-color: {COLORS["surface_raised"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    color: #e4e4e7;
    min-height: 22px;
    padding: 3px 9px;
}}
QPushButton:hover {{
    background-color: {COLORS["surface_hover"]};
    border-color: {COLORS["border_strong"]};
    color: {COLORS["text"]};
}}
QPushButton:pressed {{ background-color: {COLORS["panel"]}; }}
QPushButton:focus, QToolButton:focus {{ border: 1px solid {COLORS["focus"]}; }}
QPushButton:disabled {{
    background-color: {COLORS["surface"]};
    border-color: #202024;
    color: {COLORS["text_disabled"]};
}}
QFrame#FormatSwitch {{
    background-color: {COLORS["field"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
}}
QFrame#FormatSwitch QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 0;
    min-width: 46px;
    min-height: 22px;
    padding: 3px 10px;
}}
QFrame#FormatSwitch QPushButton:hover {{ background-color: {COLORS["surface"]}; }}
QFrame#FormatSwitch QPushButton:checked {{
    background-color: {COLORS["surface_hover"]};
    color: {COLORS["text"]};
}}
QFrame#FormatSwitch QPushButton#FormatSegmentLeft {{
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-right: 1px solid {COLORS["border"]};
}}
QFrame#FormatSwitch QPushButton#FormatSegmentRight {{
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}}
QFrame#FormatSwitch QPushButton:focus {{
    border: 1px solid {COLORS["focus"]};
}}
QPushButton#DownloadButton {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
    color: #ffffff;
    font-weight: 600;
    min-height: 24px;
    padding: 4px 12px;
}}
QPushButton#DownloadButton:hover {{
    background-color: {COLORS["accent_hover"]};
    border-color: {COLORS["accent_hover"]};
}}
QPushButton#DownloadButton:pressed {{
    background-color: {COLORS["accent_pressed"]};
    border-color: {COLORS["accent_pressed"]};
}}
QPushButton#DownloadButton:disabled {{
    background-color: {COLORS["accent_soft"]};
    border-color: #2d2341;
    color: #746987;
}}
QPushButton#CancelButton, QPushButton#PauseButton, QPushButton#SkipButton {{
    min-height: 24px;
    padding: 4px 9px;
}}

QToolButton#BrowseButton, QToolButton#OpenFolderButton, QToolButton#CookieBrowseButton {{
    background-color: {COLORS["surface_raised"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    color: {COLORS["text"]};
    min-width: 26px;
    min-height: 26px;
    padding: 2px;
}}
QToolButton#BrowseButton:hover, QToolButton#OpenFolderButton:hover, QToolButton#CookieBrowseButton:hover {{
    background-color: {COLORS["surface_hover"]};
    border-color: {COLORS["border_strong"]};
}}

QCheckBox {{
    color: {COLORS["text_muted"]};
    spacing: 6px;
    padding: 2px 1px;
}}
QCheckBox:hover, QCheckBox:focus {{ color: {COLORS["text"]}; }}
QCheckBox:disabled {{ color: {COLORS["text_disabled"]}; }}
QCheckBox::indicator {{ width: 14px; height: 14px; }}
ToggleSwitch {{ background-color: transparent; padding: 0; }}

QProgressBar {{
    background-color: {COLORS["field"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    color: {COLORS["text_muted"]};
    min-height: 16px;
    text-align: center;
}}
QProgressBar::chunk {{ background-color: {COLORS["accent"]}; border-radius: 4px; }}

QLabel#DependencyStatus, QLabel#NetworkLabel, QLabel#StatusLabel {{
    color: {COLORS["text_muted"]};
    background-color: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
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
    color: {COLORS["success"]};
}}
QLabel#DependencyStatus[state="partial"], QLabel#NetworkLabel[state="warning"], QLabel#StatusLabel[state="warning"] {{
    color: {COLORS["warning"]};
    border-color: #4a3b1f;
}}
QLabel#DependencyStatus[state="warning"], QLabel#NetworkLabel[state="error"], QLabel#StatusLabel[state="error"] {{
    color: {COLORS["danger"]};
    border-color: #4d262b;
}}
QLabel#StatusLabel[state="active"] {{ color: #ddd6fe; }}
QLabel#QueueSummary {{
    color: {COLORS["text_muted"]};
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 2px 7px;
}}
QLabel#QueueSummary[state="notice"] {{ color: {COLORS["warning"]}; border-color: #4a3b1f; }}
QLabel#QueueSummary[state="warning"] {{ color: {COLORS["danger"]}; border-color: #4d262b; }}
QPushButton#ImportUrlsButton, QPushButton#CleanUrlsButton, QPushButton#ClearUrlsButton, QPushButton#CheckNetworkButton {{
    min-height: 22px;
    padding: 3px 8px;
}}
QPlainTextEdit#LogOutput {{
    background-color: #08080a;
    border-color: #222226;
    color: #c4c4cc;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 8.5pt;
}}

QTabWidget::pane {{
    background-color: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 7px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: transparent;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    color: {COLORS["text_muted"]};
    font-weight: 500;
    min-height: 24px;
    padding: 4px 12px;
    margin-right: 2px;
}}
QTabBar::tab:hover {{ color: {COLORS["text"]}; background-color: {COLORS["surface"]}; }}
QTabBar::tab:selected {{
    color: {COLORS["text"]};
    background-color: transparent;
    border-bottom-color: {COLORS["focus"]};
}}
QTabBar::tab:focus {{ border: 1px solid {COLORS["focus"]}; }}

QGroupBox {{
    background-color: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 7px;
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
    color: #d4d4d8;
    background-color: {COLORS["panel"]};
}}
QToolButton#HelpButton {{
    background-color: {COLORS["surface_raised"]};
    border: 1px solid {COLORS["border_strong"]};
    border-radius: 13px;
    color: #c4b5fd;
    font-size: 13px;
    font-weight: 700;
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
}}
QToolButton#HelpButton:hover {{ background-color: {COLORS["surface_hover"]}; border-color: {COLORS["focus"]}; }}
QLabel#CookieTip {{ color: {COLORS["text_muted"]}; font-size: 9pt; }}

QDialog#HistoryDialog, QDialog#HelpDialog {{ background-color: {COLORS["canvas"]}; }}
QLabel#DialogTitle {{ color: {COLORS["text"]}; font-size: 13pt; font-weight: 600; }}
QTableWidget {{
    background-color: {COLORS["panel"]};
    alternate-background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    color: {COLORS["text"]};
    gridline-color: #222226;
    selection-background-color: #2e1f4f;
    selection-color: #ffffff;
}}
QTableWidget::item {{ padding: 6px; border-bottom: 1px solid #222226; }}
QTableWidget::item:selected {{ background-color: #2e1f4f; color: #ffffff; }}
QTableWidget QHeaderView::section {{
    background-color: {COLORS["surface_raised"]};
    border: none;
    border-bottom: 1px solid {COLORS["border_strong"]};
    border-right: 1px solid {COLORS["border"]};
    color: #d4d4d8;
    font-weight: 600;
    padding: 7px;
}}
QTextBrowser {{ padding: 10px; }}
QScrollBar:vertical {{ background: {COLORS["canvas"]}; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {COLORS["border_strong"]}; min-height: 24px; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: #52525b; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
