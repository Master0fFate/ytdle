"""Angelcore skin (reference-monochrome profile).

Near-black field, square geometry, one mono family, neutral inks only.
Regions are split by single hairlines; controls get no resting box. Fields
carry one bottom rule. Hover is a small surface change, focus a 2 px outline.
The one filled control is the dominant action (Download).
"""

_MONO = "'Cascadia Mono', Consolas, 'Courier New', monospace"


def build(c: dict, arrow_path: str = "") -> str:
    arrow = (
        f"QComboBox::down-arrow {{ image: url({arrow_path}); width: 10px; height: 10px; }}"
        if arrow_path
        else ""
    )
    return f"""
QWidget {{ color: {c['text']}; font-family: {_MONO}; font-size: 13px; }}
QMainWindow#MainWindow, QDialog, QMessageBox {{ background: {c['bg']}; color: {c['text']}; }}
QLabel {{ background: transparent; }}
QLabel:disabled {{ color: {c['icon_disabled']}; }}
QToolTip {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['rule']};
    border-radius: 0; padding: 4px 8px; }}
QMenu {{ background: {c['surface']}; border: 1px solid {c['rule']}; border-radius: 0; padding: 4px 0; }}
QMenu::item {{ padding: 4px 12px; }}
QMenu::item:selected {{ background: {c['selected']}; color: {c['strong']}; }}
QFrame {{ border: none; border-radius: 0; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QAbstractScrollArea::corner {{ background: transparent; border: none; }}

/* Title bar: one rule under it, current page marked with "> " */
#TitleBar {{ background: transparent; border-bottom: 1px solid {c['rule']}; }}
QLabel#BrandName {{ font-size: 14px; font-weight: 700; color: {c['strong']}; }}
QFrame#NavBar {{ background: transparent; }}
QPushButton#NavButton {{ background: transparent; color: {c['muted']}; border: none;
    border-radius: 0; min-height: 28px; max-height: 28px; padding: 0 8px; }}
QPushButton#NavButton:hover {{ background: {c['selected']}; color: {c['strong']}; }}
QPushButton#NavButton:checked {{ color: {c['strong']}; font-weight: 700; }}
QPushButton#NavButton:focus {{ border: 2px solid {c['strong']}; }}
QLabel#NetworkLabel {{ background: transparent; color: {c['muted']}; padding: 0 4px;
    min-height: 28px; max-height: 28px; }}
QLabel#NetworkLabel[state="error"] {{ color: {c['strong']}; }}

/* Fields: no box, one bottom hairline */
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: transparent; color: {c['text']}; border: none;
    border-bottom: 1px solid {c['rule']}; border-radius: 0;
    selection-background-color: {c['strong']}; selection-color: {c['bg']};
}}
QLineEdit, QComboBox {{ min-height: 28px; padding: 0 4px; }}
QPlainTextEdit {{ padding: 4px; }}
QLineEdit:hover, QComboBox:hover {{ background: {c['surface']}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    border-bottom: 1px solid {c['strong']}; }}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    color: {c['icon_disabled']}; border-bottom: 1px solid {c['rule']}; }}
QComboBox {{ padding-right: 20px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
    width: 20px; border: none; }}
{arrow}
QComboBox QAbstractItemView {{ background: {c['surface']}; color: {c['text']};
    border: 1px solid {c['rule']}; border-radius: 0; outline: 0;
    selection-background-color: {c['selected']}; selection-color: {c['strong']}; }}

/* Actions: words on open ground, no resting border */
QPushButton, QToolButton {{ background: transparent; color: {c['text']}; border: none;
    border-radius: 0; min-height: 28px; padding: 0 6px; }}
QPushButton:hover, QToolButton:hover {{ background: {c['selected']}; color: {c['strong']}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {c['rule']}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {c['strong']}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c['icon_disabled']}; background: transparent; }}
QPushButton[iconAction="true"], QToolButton#BrowseButton, QToolButton#OpenFolderButton,
QToolButton#CookieBrowseButton, QToolButton#HelpButton {{
    min-width: 0; max-width: 480px; min-height: 28px; max-height: 28px; padding: 0 6px; }}
QToolButton#MinimizeButton, QToolButton#CloseButton {{ min-width: 32px; max-width: 32px;
    min-height: 32px; max-height: 32px; padding: 0; }}
QPushButton#DownloadButton {{ background: {c['accent']}; color: {c['on_accent']};
    font-weight: 700; min-width: 132px; min-height: 32px; max-height: 32px; padding: 0 14px; }}
QPushButton#DownloadButton:hover {{ background: {c['accent_hover']}; color: {c['on_accent']}; }}
QPushButton#DownloadButton:pressed {{ background: {c['accent_pressed']}; }}
QPushButton#DownloadButton:focus {{ border: 2px solid {c['outline']}; }}
QPushButton#DownloadButton:disabled {{ background: {c['selected']}; color: {c['icon_disabled']}; }}
QPushButton#CancelButton {{ color: {c['strong']}; min-height: 32px; max-height: 32px; }}
QPushButton#PasteButton {{ min-height: 28px; max-height: 28px; }}

/* Segments: plain words, the checked one strong with its own rule */
QFrame[segmented="true"] {{ background: transparent; }}
QFrame[segmented="true"] QPushButton {{ background: transparent; color: {c['muted']}; border: none;
    border-bottom: 1px solid {c['rule']}; min-width: 44px; min-height: 28px; max-height: 28px;
    padding: 0 10px; }}
QFrame[segmented="true"] QPushButton:hover {{ background: {c['selected']}; color: {c['strong']}; }}
QFrame[segmented="true"] QPushButton:checked {{ color: {c['strong']}; font-weight: 700;
    border-bottom: 1px solid {c['strong']}; }}
QFrame[segmented="true"] QPushButton:focus {{ border: 2px solid {c['strong']}; }}
QFrame#ActivitySwitch QPushButton {{ min-height: 24px; max-height: 24px; padding: 0 8px; }}
ToggleSwitch {{ background: transparent; }}

/* Regions: one hairline on top, no boxes */
QFrame#Card, QFrame#ActionCard {{ background: transparent; border-top: 1px solid {c['rule']}; }}
QFrame#DropZone {{ background: transparent; border: none; }}
QFrame#DropZone[state="drag"] {{ background: {c['selected']}; border: 1px solid {c['outline']}; }}
QFrame#DropZone QPlainTextEdit, QFrame#DropZone QPlainTextEdit:hover,
QFrame#DropZone QPlainTextEdit:focus, QFrame#DropZone QPlainTextEdit:disabled {{
    background: transparent; border: none; border-top: 1px solid {c['rule']};
    border-bottom: 1px solid {c['rule']}; padding: 4px 0; }}
QFrame#DropZone QPlainTextEdit:focus {{ border-bottom: 1px solid {c['strong']}; }}
QLabel#SectionTitle {{ color: {c['strong']}; font-weight: 700; }}
QLabel#SectionHint, QLabel#FieldHint, QLabel#EmptyHint {{ color: {c['muted']}; font-size: 12px; }}
QLabel#FieldLabel {{ color: {c['muted']}; }}
QLabel#EmptyTitle {{ color: {c['strong']}; }}
QLabel#QueueSummary {{ color: {c['muted']}; background: transparent; padding: 0 4px; font-size: 12px; }}
QLabel#QueueSummary[state="warning"] {{ color: {c['strong']}; }}
QLabel#StatusLabel {{ color: {c['strong']}; font-size: 15px; font-weight: 700; }}
QLabel#StatusDetail {{ color: {c['muted']}; font-size: 12px; }}
QLabel#DependencyStatus {{ color: {c['text']}; }}

QProgressBar {{ background: {c['rule']}; border: none; border-radius: 0;
    min-height: 2px; max-height: 2px; }}
QProgressBar::chunk {{ background: {c['text']}; border-radius: 0; }}
QPlainTextEdit#LogOutput, QPlainTextEdit#LogOutput:hover, QPlainTextEdit#LogOutput:focus {{
    background: transparent; color: {c['text']}; border: none; font-size: 12px; padding: 2px 0; }}
QListWidget#SessionList {{ background: transparent; border: none; outline: 0; }}

QTabWidget::pane {{ background: {c['bg']}; border: none; border-top: 1px solid {c['rule']}; }}
QDialog#HistoryDialog QTabWidget::pane {{ top: 4px; }}
QTabBar::tab {{ background: transparent; color: {c['muted']}; border: none; border-radius: 0;
    min-height: 26px; padding: 0 12px; }}
QTabBar::tab:hover {{ background: {c['selected']}; color: {c['strong']}; }}
QTabBar::tab:selected {{ color: {c['strong']}; font-weight: 700; border-bottom: 1px solid {c['strong']}; }}
QLabel#CookieTip, QLabel#HistoryNote {{ color: {c['muted']}; font-size: 12px; }}
QLabel#DialogTitle {{ color: {c['strong']}; font-size: 18px; font-weight: 700; }}
QTableWidget {{ background: transparent; alternate-background-color: {c['bg']}; border: none;
    gridline-color: {c['rule']}; selection-background-color: {c['selected']};
    selection-color: {c['strong']}; }}
QTableWidget::item {{ padding: 4px; }}
QTableWidget QHeaderView::section {{ background: transparent; color: {c['muted']}; border: none;
    border-bottom: 1px solid {c['rule']}; padding: 4px; }}
QTextBrowser {{ padding: 8px; }}
QScrollBar:vertical, QScrollBar:horizontal {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 8px; }}
QScrollBar:horizontal {{ height: 8px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background: {c['rule']};
    border: none; border-radius: 0; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {c['outline']}; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; }}
"""
