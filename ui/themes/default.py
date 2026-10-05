"""Default skin: YTDLE's own soft-purple, rounded dark look."""

from ui.themes import combo_arrow, state_rules


def build(c: dict, arrow_path: str = "") -> str:
    return f"""
QMainWindow#MainWindow, QDialog, QMessageBox {{
    background: {c['bg']}; color: {c['text']};
    font-family: Roboto, 'Segoe UI', Arial, sans-serif; font-size: 10pt;
}}
QWidget {{ color: {c['text']}; }}
QLabel {{ color: {c['text']}; background: transparent; }}
QLabel:disabled {{ color: {c['muted']}; }}
QToolTip {{ background: {c['raised']}; color: {c['text']};
    border: none; border-radius: 8px; padding: 6px 10px; }}
QMenu {{ background: {c['container']}; border: none;
    border-radius: 12px; padding: 5px; }}
QMenu::item {{ padding: 7px 18px; border-radius: 8px; }}
QMenu::item:selected {{ background: {c['raised']}; }}
QMenu::item:disabled {{ color: {c['muted']}; }}
QMenu::separator {{ height: 1px; background: {c['rule']}; margin: 4px 8px; }}
QFrame {{ border: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QAbstractScrollArea::corner {{ background: transparent; border: none; }}

/* Title bar and navigation */
#TitleBar {{ background: transparent; }}
QLabel#BrandName {{ font-size: 12pt; font-weight: 800; color: {c['strong']}; }}
QFrame#NavBar {{ background: {c['surface']}; border-radius: 20px; }}
QPushButton#NavButton {{ background: transparent; color: {c['muted']};
    border: 1px solid transparent; border-radius: 17px;
    min-height: 32px; max-height: 32px; padding: 0 16px; font-weight: 600; }}
QPushButton#NavButton:hover {{ background: {c['container']}; color: {c['text']}; }}
QPushButton#NavButton:checked {{ background: {c['selected']}; color: {c['on_selected']}; }}
QPushButton#NavButton:focus {{ border: 2px solid {c['focus']}; }}
QLabel#NetworkLabel {{ background: {c['surface']}; border-radius: 15px;
    min-height: 30px; max-height: 30px; padding: 0 12px; font-weight: 600; }}
{state_rules(c, 'QLabel#NetworkLabel', 'color')}

/* Fields */
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: {c['field']}; color: {c['text']};
    border: 1px solid transparent; border-bottom: 1px solid {c['rule']};
    border-radius: 18px;
    selection-background-color: {c['primary_container']};
    selection-color: {c['text']};
}}
QLineEdit, QComboBox {{ min-height: 30px; padding: 2px 12px; }}
QPlainTextEdit {{ padding: 8px 11px; }}
QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextBrowser:hover {{
    background: {c['container']}; border-bottom: 1px solid {c['outline']}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    background: {c['container']}; border-bottom: 2px solid {c['accent']}; }}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    background: {c['field']}; color: {c['muted']};
    border-bottom: 1px solid transparent; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
    width: 28px; border: none; }}
{combo_arrow(arrow_path)}
QComboBox QAbstractItemView {{ background: {c['container']}; color: {c['text']};
    border: none; border-radius: 12px; outline: 0;
    selection-background-color: {c['primary_container']}; padding: 5px; }}

/* Buttons */
QPushButton, QToolButton {{
    background: {c['container']}; color: {c['text']};
    border: 1px solid transparent; border-radius: 18px;
    min-height: 32px; padding: 2px 14px; font-weight: 600;
}}
QPushButton:hover, QToolButton:hover {{ background: {c['raised']}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {c['primary_container']}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {c['focus']}; }}
QPushButton:disabled, QToolButton:disabled {{ background: {c['surface']};
    color: {c['muted']}; }}
QPushButton[iconAction="true"] {{ min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px; padding: 0; border-radius: 19px; }}
QPushButton[quiet="true"] {{ background: transparent; }}
QPushButton[quiet="true"]:hover {{ background: {c['container']}; }}
QPushButton[quiet="true"]:disabled {{ background: transparent; }}
QPushButton#DownloadButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent']}, stop:1 {c['accent_end']});
    color: {c['on_accent']}; font-size: 11pt; font-weight: 700;
    min-width: 132px; min-height: 42px; max-height: 42px;
    border-radius: 21px; padding: 0 22px; }}
QPushButton#DownloadButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent_hover']}, stop:1 #b273fa); }}
QPushButton#DownloadButton:pressed {{ background: {c['accent_pressed']}; }}
QPushButton#DownloadButton:focus {{ border: 2px solid {c['strong']}; }}
QPushButton#DownloadButton:disabled {{ background: {c['container']}; color: {c['muted']}; }}
QPushButton#CancelButton {{ min-height: 38px; max-height: 38px; border-radius: 19px;
    padding: 0 16px; }}
QPushButton#CancelButton:hover {{ background: #4a2a35; color: {c['strong']}; }}
QPushButton#PasteButton {{ min-height: 32px; max-height: 32px; border-radius: 16px;
    padding: 0 14px 0 10px; }}

/* Segmented controls */
QFrame[segmented="true"] {{ border: none; border-radius: 18px; background: {c['container']}; }}
QFrame[segmented="true"] QPushButton {{ background: transparent; border: none;
    border-radius: 0; min-width: 54px; min-height: 34px; max-height: 34px; padding: 0 14px; }}
QFrame[segmented="true"] QPushButton:hover {{ background: {c['raised']}; }}
QFrame[segmented="true"] QPushButton:checked {{ background: {c['selected']};
    color: {c['on_selected']}; }}
QFrame[segmented="true"] QPushButton[segment="left"] {{ border-top-left-radius: 17px;
    border-bottom-left-radius: 17px; }}
QFrame[segmented="true"] QPushButton[segment="right"] {{ border-top-right-radius: 17px;
    border-bottom-right-radius: 17px; }}
QFrame[segmented="true"] QPushButton:focus {{ border: 2px solid {c['focus']}; }}
QFrame#ActivitySwitch QPushButton {{ min-height: 28px; max-height: 28px; min-width: 44px;
    padding: 0 12px; font-size: 9pt; }}
QFrame#ActivitySwitch {{ border-radius: 15px; }}
QFrame#ActivitySwitch QPushButton[segment="left"] {{ border-top-left-radius: 14px;
    border-bottom-left-radius: 14px; }}
QFrame#ActivitySwitch QPushButton[segment="right"] {{ border-top-right-radius: 14px;
    border-bottom-right-radius: 14px; }}

QToolButton#BrowseButton, QToolButton#OpenFolderButton,
QToolButton#CookieBrowseButton, QToolButton#HelpButton,
QToolButton#MinimizeButton, QToolButton#CloseButton {{
    min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px;
    border-radius: 19px; padding: 0; }}
QToolButton#MinimizeButton, QToolButton#CloseButton {{ background: transparent; }}
QToolButton#MinimizeButton:hover {{ background: {c['container']}; }}
QToolButton#CloseButton:hover {{ background: #5b2633; }}
QCheckBox {{ spacing: 7px; padding: 3px 2px; }}
QCheckBox:disabled {{ color: {c['muted']}; }}
ToggleSwitch {{ background: transparent; }}

/* Cards and typography */
QFrame#Card, QFrame#ActionCard {{ background: {c['surface']}; border-radius: 20px; }}
QFrame#DropZone {{ background: {c['surface']}; border: 1px dashed {c['rule']};
    border-radius: 20px; }}
QFrame#DropZone[state="filled"] {{ border: 1px solid transparent; }}
QFrame#DropZone[state="focus"] {{ border: 1px solid {c['primary_container']}; }}
QFrame#DropZone[state="drag"] {{ background: {c['accent_soft']};
    border: 2px dashed {c['focus']}; }}
QFrame#DropZone QPlainTextEdit, QFrame#DropZone QPlainTextEdit:hover,
QFrame#DropZone QPlainTextEdit:focus {{ background: transparent; border: none;
    padding: 2px 0; }}
QFrame#DropZone QPlainTextEdit:disabled {{ background: transparent; border: none; }}
QLabel#SectionTitle {{ font-size: 10.5pt; font-weight: 700; color: {c['strong']}; }}
QLabel#SectionHint, QLabel#FieldHint {{ color: {c['muted']}; font-size: 9pt; }}
QLabel#FieldLabel {{ color: {c['muted']}; font-weight: 600; }}
QLabel#EmptyTitle {{ font-size: 12.5pt; font-weight: 700; color: {c['text']}; }}
QLabel#EmptyHint {{ color: {c['muted']}; font-size: 9pt; }}
QLabel#QueueSummary {{ color: {c['muted']}; background: {c['container']};
    border-radius: 11px; padding: 2px 10px; font-size: 9pt; font-weight: 600; }}
QLabel#QueueSummary[state="warning"] {{ color: {c['warning']}; }}
QLabel#QueueSummary[state="notice"] {{ color: {c['text']}; }}
QLabel#StatusLabel {{ font-size: 12pt; font-weight: 700; color: {c['strong']}; }}
QLabel#StatusDetail {{ color: {c['muted']}; }}
QLabel#StatusDot {{ border-radius: 5px; background: {c['outline']}; }}
{state_rules(c, 'QLabel#StatusDot', 'background')}
QLabel#DependencyStatus {{ color: {c['text']}; }}
{state_rules(c, 'QLabel#DependencyStatus', 'color')}
QLabel#DependencyStatus[state="ready"] {{ color: {c['success']}; }}

QProgressBar {{ background: {c['container']}; border: none; border-radius: 3px;
    min-height: 6px; max-height: 6px; }}
QProgressBar::chunk {{ border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {c['accent']}, stop:1 {c['focus']}); }}
QPlainTextEdit#LogOutput {{ background: transparent; color: {c['text']};
    border: none; border-radius: 0; padding: 2px 0;
    font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; }}
QPlainTextEdit#LogOutput:hover, QPlainTextEdit#LogOutput:focus {{
    background: transparent; border: none; }}
QListWidget#SessionList {{ background: transparent; border: none; outline: 0; }}

QTabWidget::pane {{ background: {c['bg']}; border: none; }}
QDialog#HistoryDialog QTabWidget::pane {{ top: 12px; }}
QTabBar::tab {{ background: transparent; border: 1px solid transparent;
    border-radius: 16px; color: {c['muted']}; font-weight: 600;
    min-height: 30px; padding: 3px 18px; margin-right: 5px; }}
QTabBar::tab:hover {{ background: {c['container']}; color: {c['text']}; }}
QTabBar::tab:selected {{ background: {c['selected']}; color: {c['on_selected']}; }}
QTabBar::tab:focus {{ border: 2px solid {c['focus']}; }}
QLabel#CookieTip {{ color: {c['muted']}; }}
QLabel#DialogTitle {{ font-size: 16pt; font-weight: 700; color: {c['strong']}; }}
QLabel#HistoryNote {{ color: {c['muted']}; }}
QTableWidget {{ background: {c['surface']}; alternate-background-color: {c['container']};
    border: none; border-radius: 12px; gridline-color: {c['container']};
    selection-background-color: {c['primary_container']}; }}
QTableWidget::item {{ padding: 6px; }}
QTableWidget::item:selected {{ background: {c['primary_container']}; }}
QTableWidget QHeaderView::section {{ background: {c['container']};
    border: none; color: {c['text']}; font-weight: 600; padding: 7px; }}
QTextBrowser {{ padding: 10px; }}
QScrollBar:vertical, QScrollBar:horizontal {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 12px; margin: 2px 0; }}
QScrollBar:horizontal {{ height: 12px; margin: 0 2px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: #4a4558; border: 3px solid transparent; border-radius: 6px;
    min-height: 36px; min-width: 36px; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background: #a68acb; }}
QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {{
    background: {c['accent']}; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0;
    background: transparent; border: none; }}
"""
