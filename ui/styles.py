"""Material 3 Expressive-inspired dark Qt theme with YTDLE's original purple.

Qt widgets use a Fusion/QSS adaptation of Material's semantic dark color roles,
variable rounded shapes, tonal surfaces, segmented selection and visible states.
"""

COLORS = {
    "bg": "#101018",                # surface
    "surface": "#191921",           # surface container low
    "container": "#25242e",         # surface container
    "raised": "#302f3a",            # surface container high
    "field": "#1d1c26",             # surface container lowest for inputs
    "rule": "#494653",              # outline variant
    "outline": "#918d9c",           # outline
    "muted": "#aaa7b7",             # on-surface variant
    "text": "#e8e6f0",              # on-surface
    "strong": "#ffffff",            # on-primary
    "accent": "#7c3aed",            # original brand primary
    "accent_hover": "#8b50f4",
    "accent_pressed": "#6830cb",
    "primary_container": "#493177",
    "focus": "#bd9bff",
}

STYLESHEET = f"""
QMainWindow#MainWindow, QDialog, QMessageBox {{
    background: {COLORS['bg']}; color: {COLORS['text']};
    font-family: Roboto, 'Segoe UI', Arial, sans-serif; font-size: 10pt;
}}
QWidget {{ color: {COLORS['text']}; }}
QLabel {{ color: {COLORS['text']}; }}
QLabel:disabled {{ color: {COLORS['muted']}; }}
QToolTip {{ background: {COLORS['raised']}; color: {COLORS['text']};
    border: none; border-radius: 8px; padding: 6px 10px; }}
QMenu {{ background: {COLORS['container']}; border: none;
    border-radius: 12px; padding: 5px; }}
QMenu::item {{ padding: 7px 18px; border-radius: 8px; }}
QMenu::item:selected {{ background: {COLORS['raised']}; }}
QMenu::item:disabled {{ color: {COLORS['muted']}; }}
QMenu::separator {{ height: 1px; background: {COLORS['rule']}; margin: 4px 8px; }}
#TitleBar {{ background: {COLORS['surface']}; border: none; border-radius: 16px; }}
#TitleBar QLabel#WindowTitle {{ color: {COLORS['text']}; font-size: 11pt; font-weight: 700; }}
QFrame {{ border: none; }}
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: {COLORS['field']}; color: {COLORS['text']};
    border: 1px solid transparent; border-bottom: 1px solid {COLORS['rule']};
    border-radius: 18px;
    selection-background-color: {COLORS['primary_container']};
    selection-color: {COLORS['text']};
}}
QLineEdit, QComboBox {{ min-height: 30px; padding: 2px 11px; }}
QPlainTextEdit {{ padding: 8px 11px; }}
QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextBrowser:hover {{
    background: {COLORS['container']}; border-bottom: 1px solid {COLORS['outline']}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    background: {COLORS['container']}; border-bottom: 2px solid {COLORS['accent']}; }}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    background: {COLORS['surface']}; color: {COLORS['muted']};
    border-bottom: 1px solid {COLORS['surface']}; }}
QComboBox {{ padding-right: 24px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
    width: 24px; border: none; }}
QComboBox QAbstractItemView {{ background: {COLORS['container']}; color: {COLORS['text']};
    border: none; border-radius: 12px; outline: 0;
    selection-background-color: {COLORS['primary_container']}; padding: 5px; }}
QPushButton, QToolButton {{
    background: {COLORS['container']}; color: {COLORS['text']};
    border: 1px solid transparent; border-radius: 18px;
    min-height: 32px; padding: 2px 14px; font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{ background: {COLORS['raised']}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {COLORS['primary_container']}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {COLORS['focus']}; }}
QPushButton:disabled, QToolButton:disabled {{ background: {COLORS['surface']};
    color: {COLORS['muted']}; }}
QPushButton[iconAction="true"] {{ min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px; padding: 0; border-radius: 19px; }}
QPushButton#DownloadButton {{ background: {COLORS['accent']}; color: {COLORS['strong']};
    min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px;
    border-radius: 19px; padding: 0; }}
QPushButton#DownloadButton:hover {{ background: {COLORS['accent_hover']}; }}
QPushButton#DownloadButton:pressed {{ background: {COLORS['accent_pressed']}; }}
QPushButton#DownloadButton:disabled {{ background: {COLORS['surface']}; color: {COLORS['muted']}; }}
QFrame#FormatSwitch {{ border: none; border-radius: 18px;
    background: {COLORS['container']}; }}
QFrame#FormatSwitch QPushButton {{ background: transparent; border: none;
    border-radius: 0; min-width: 54px; min-height: 32px; padding: 2px 10px; }}
QFrame#FormatSwitch QPushButton:hover {{ background: {COLORS['raised']}; }}
QFrame#FormatSwitch QPushButton:checked {{ background: {COLORS['primary_container']};
    color: {COLORS['strong']}; }}
QFrame#FormatSwitch QPushButton#FormatSegmentLeft {{ border-top-left-radius: 17px;
    border-bottom-left-radius: 17px; }}
QFrame#FormatSwitch QPushButton#FormatSegmentRight {{ border-top-right-radius: 17px;
    border-bottom-right-radius: 17px; }}
QFrame#FormatSwitch QPushButton:focus {{ border: 2px solid {COLORS['focus']}; }}
QToolButton#BrowseButton, QToolButton#OpenFolderButton,
QToolButton#CookieBrowseButton, QToolButton#HelpButton,
QToolButton#MinimizeButton, QToolButton#CloseButton {{
    min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px;
    border-radius: 19px; padding: 0; }}
QToolButton#CloseButton:hover {{ background: {COLORS['primary_container']}; }}
QCheckBox {{ spacing: 7px; padding: 3px 2px; }}
QCheckBox:disabled {{ color: {COLORS['muted']}; }}
ToggleSwitch {{ background: transparent; }}
QProgressBar {{ background: {COLORS['container']}; border: none; border-radius: 8px;
    color: {COLORS['text']}; min-height: 16px; text-align: center; }}
QProgressBar::chunk {{ background: {COLORS['accent']}; border-radius: 8px; }}
QLabel#QueueSummary {{ color: {COLORS['muted']}; padding: 2px 5px; }}
QLabel#QueueSummary[state="warning"], QLabel#QueueSummary[state="notice"] {{
    color: {COLORS['text']}; }}
QPlainTextEdit#LogOutput {{ background: {COLORS['surface']}; color: {COLORS['text']};
    border: none; border-radius: 16px;
    font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; }}
QTabWidget::pane {{ background: {COLORS['bg']}; border: none; }}
QDialog#HistoryDialog QTabWidget::pane {{ top: 12px; }}
QTabBar::tab {{ background: transparent; border: 1px solid transparent;
    border-radius: 16px; color: {COLORS['muted']}; font-weight: 600;
    min-height: 30px; padding: 3px 18px; margin-right: 5px; }}
QTabBar::tab:hover {{ background: {COLORS['container']}; color: {COLORS['text']}; }}
QTabBar::tab:selected {{ background: {COLORS['primary_container']}; color: {COLORS['strong']}; }}
QTabBar::tab:focus {{ border: 2px solid {COLORS['focus']}; }}
QGroupBox {{ background: {COLORS['surface']}; border: none;
    border-radius: 18px; color: {COLORS['text']}; font-weight: 600;
    margin-top: 15px; padding: 16px 12px 12px; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; padding: 0 7px; background: {COLORS['surface']}; }}
QLabel#CookieTip {{ color: {COLORS['muted']}; }}
QLabel#DialogTitle {{ font-size: 16pt; font-weight: 700; }}
QTableWidget {{ background: {COLORS['surface']}; alternate-background-color: {COLORS['container']};
    border: none; border-radius: 12px; gridline-color: {COLORS['container']};
    selection-background-color: {COLORS['primary_container']}; }}
QTableWidget::item {{ padding: 6px; }}
QTableWidget::item:selected {{ background: {COLORS['primary_container']}; }}
QTableWidget QHeaderView::section {{ background: {COLORS['container']};
    border: none; color: {COLORS['text']}; font-weight: 600; padding: 7px; }}
QTextBrowser {{ padding: 10px; }}
QScrollBar:vertical, QScrollBar:horizontal {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 14px; margin: 2px 0; }}
QScrollBar:horizontal {{ height: 14px; margin: 0 2px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #5a5469; border: 3px solid {COLORS['surface']}; border-radius: 7px;
    min-height: 36px; min-width: 36px; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: #a68acb; }}
QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
    background: {COLORS['accent']}; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0;
    background: transparent; border: none; }}
"""


def strip_native_frames(root) -> None:
    """Prevent Windows bevels from painting over Qt-styled controls."""
    from PySide6.QtWidgets import QFrame, QLineEdit, QPlainTextEdit, QTextBrowser

    for widget in root.findChildren(QLineEdit):
        widget.setFrame(False)
    for widget in root.findChildren(QPlainTextEdit):
        widget.setFrameStyle(QFrame.Shape.NoFrame)
    for widget in root.findChildren(QTextBrowser):
        widget.setFrameStyle(QFrame.Shape.NoFrame)


def apply_chrome(app) -> None:
    """Apply a dark Fusion palette to native popups as well as styled widgets."""
    import sys
    from pathlib import Path

    from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette

    font_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    font_path = font_root / 'assets' / 'Roboto.ttf'
    if font_path.is_file() and QFontDatabase.addApplicationFont(str(font_path)) >= 0:
        app.setFont(QFont('Roboto', 10))
    app.setStyle('Fusion')
    palette = app.palette()
    ink = {
        QPalette.ColorRole.Window: COLORS['bg'],
        QPalette.ColorRole.Base: COLORS['field'],
        QPalette.ColorRole.AlternateBase: COLORS['container'],
        QPalette.ColorRole.Button: COLORS['container'],
        QPalette.ColorRole.ButtonText: COLORS['text'],
        QPalette.ColorRole.WindowText: COLORS['text'],
        QPalette.ColorRole.Text: COLORS['text'],
        QPalette.ColorRole.PlaceholderText: COLORS['muted'],
        QPalette.ColorRole.BrightText: COLORS['strong'],
        QPalette.ColorRole.Light: COLORS['raised'],
        QPalette.ColorRole.Midlight: COLORS['container'],
        QPalette.ColorRole.Mid: COLORS['rule'],
        QPalette.ColorRole.Dark: COLORS['bg'],
        QPalette.ColorRole.Shadow: COLORS['bg'],
        QPalette.ColorRole.Highlight: COLORS['primary_container'],
        QPalette.ColorRole.HighlightedText: COLORS['strong'],
        QPalette.ColorRole.ToolTipBase: COLORS['raised'],
        QPalette.ColorRole.ToolTipText: COLORS['text'],
    }
    for role, color in ink.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
