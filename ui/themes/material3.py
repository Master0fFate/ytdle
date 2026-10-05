"""Material 3 skin: the dark scheme and component shapes from the M3 spec.

Filled text fields (top corners only, active indicator), primary tabs with an
underline indicator, a filled primary button, outlined segmented buttons,
tonal buttons for secondary actions, 12 px cards, and a 4 px linear indicator.
"""

from ui.themes import combo_arrow, state_rules

# State layers: onSurface at 8% (hover) and 10% (pressed) over the surface below.
_HOVER = "rgba(230, 224, 233, 20)"
_PRESS = "rgba(230, 224, 233, 26)"


def build(c: dict, arrow_path: str = "") -> str:
    return f"""
QMainWindow#MainWindow, QDialog, QMessageBox {{
    background: {c['bg']}; color: {c['text']};
    font-family: Roboto, 'Segoe UI', Arial, sans-serif; font-size: 10pt;
}}
QWidget {{ color: {c['text']}; }}
QLabel {{ color: {c['text']}; background: transparent; }}
QLabel:disabled {{ color: {c['icon_disabled']}; }}
QToolTip {{ background: {c['text']}; color: #322f35; border: none;
    border-radius: 4px; padding: 4px 8px; }}
QMenu {{ background: {c['container']}; border: none; border-radius: 4px; padding: 8px 0; }}
QMenu::item {{ padding: 8px 16px; }}
QMenu::item:selected {{ background: {_HOVER}; }}
QFrame {{ border: none; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QAbstractScrollArea::corner {{ background: transparent; border: none; }}

/* Top app bar with primary tabs */
#TitleBar {{ background: transparent; }}
QLabel#BrandName {{ font-size: 13pt; font-weight: 500; color: {c['text']}; }}
QFrame#NavBar {{ background: transparent; border: none; }}
QPushButton#NavButton {{ background: transparent; color: {c['muted']};
    border: none; border-bottom: 3px solid transparent; border-radius: 0;
    min-height: 28px; max-height: 28px; padding: 0 16px; font-weight: 500; }}
QPushButton#NavButton:hover {{ background: {_HOVER}; color: {c['text']}; }}
QPushButton#NavButton:checked {{ color: {c['accent']}; border-bottom: 3px solid {c['accent']}; }}
QPushButton#NavButton:focus {{ border: 2px solid {c['focus']}; }}
QLabel#NetworkLabel {{ background: transparent; border: 1px solid {c['outline']};
    border-radius: 8px; min-height: 30px; max-height: 30px; padding: 0 12px;
    font-weight: 500; }}
{state_rules(c, 'QLabel#NetworkLabel', 'color')}

/* Filled text fields */
QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: {c['field']}; color: {c['text']}; border: none;
    border-bottom: 1px solid {c['muted']};
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    border-bottom-left-radius: 0; border-bottom-right-radius: 0;
    selection-background-color: {c['primary_container']}; selection-color: {c['text']};
}}
QLineEdit, QComboBox {{ min-height: 32px; padding: 2px 12px; }}
QPlainTextEdit {{ padding: 8px 12px; }}
QLineEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextBrowser:hover {{
    background: #3d3a42; border-bottom: 1px solid {c['text']}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextBrowser:focus {{
    border-bottom: 2px solid {c['accent']}; }}
QLineEdit:disabled, QComboBox:disabled, QPlainTextEdit:disabled {{
    background: #26242b; color: {c['icon_disabled']};
    border-bottom: 1px solid {c['rule']}; }}
QComboBox {{ padding-right: 30px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
    width: 30px; border: none; }}
{combo_arrow(arrow_path)}
QComboBox QAbstractItemView {{ background: {c['container']}; color: {c['text']};
    border: none; border-radius: 4px; outline: 0;
    selection-background-color: {c['selected']}; padding: 8px 0; }}

/* Buttons: outlined by default, standard icon buttons, filled primary, tonal */
QPushButton, QToolButton {{
    background: transparent; color: {c['accent']};
    border: 1px solid {c['outline']}; border-radius: 18px;
    min-height: 32px; padding: 2px 16px; font-weight: 500;
}}
QPushButton:hover, QToolButton:hover {{ background: {_HOVER}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {_PRESS}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {c['focus']}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {c['icon_disabled']};
    border-color: {c['rule']}; }}
QPushButton[iconAction="true"], QToolButton#BrowseButton, QToolButton#OpenFolderButton,
QToolButton#CookieBrowseButton, QToolButton#HelpButton,
QToolButton#MinimizeButton, QToolButton#CloseButton {{
    background: transparent; border: none;
    min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px;
    padding: 0; border-radius: 20px; }}
QPushButton[iconAction="true"]:hover, QToolButton#BrowseButton:hover,
QToolButton#OpenFolderButton:hover, QToolButton#CookieBrowseButton:hover,
QToolButton#HelpButton:hover, QToolButton#MinimizeButton:hover {{ background: {_HOVER}; }}
QPushButton[iconAction="true"]:focus, QToolButton:focus {{ border: 2px solid {c['focus']}; }}
QToolButton#CloseButton:hover {{ background: #8c1d18; }}
QPushButton#DownloadButton {{ background: {c['accent']}; color: {c['on_accent']};
    border: none; font-size: 10.5pt; font-weight: 500;
    min-width: 132px; min-height: 40px; max-height: 40px;
    border-radius: 20px; padding: 0 24px 0 16px; }}
QPushButton#DownloadButton:hover {{ background: {c['accent_hover']}; }}
QPushButton#DownloadButton:pressed {{ background: {c['accent_pressed']}; }}
QPushButton#DownloadButton:focus {{ border: 2px solid {c['text']}; }}
QPushButton#DownloadButton:disabled {{ background: #2f2c33; color: {c['icon_disabled']}; }}
QPushButton#CancelButton, QPushButton#PasteButton {{
    background: {c['selected']}; color: {c['on_selected']}; border: none;
    border-radius: 20px; padding: 0 16px 0 12px; }}
QPushButton#CancelButton {{ min-height: 40px; max-height: 40px; }}
QPushButton#PasteButton {{ min-height: 32px; max-height: 32px; border-radius: 16px; }}
QPushButton#CancelButton:hover, QPushButton#PasteButton:hover {{ background: #554f63; }}
QPushButton#CancelButton:focus, QPushButton#PasteButton:focus {{ border: 2px solid {c['focus']}; }}
QPushButton#CancelButton:disabled, QPushButton#PasteButton:disabled {{
    background: #2f2c33; color: {c['icon_disabled']}; }}

/* Segmented buttons: one outline, selected segment in secondary container */
QFrame[segmented="true"] {{ background: transparent; border: 1px solid {c['outline']};
    border-radius: 18px; }}
QFrame[segmented="true"] QPushButton {{ background: transparent; color: {c['text']};
    border: none; border-radius: 0; min-width: 56px; min-height: 34px; max-height: 34px;
    padding: 0 14px; }}
QFrame[segmented="true"] QPushButton[segment="right"] {{ border-left: 1px solid {c['outline']}; }}
QFrame[segmented="true"] QPushButton:hover {{ background: {_HOVER}; }}
QFrame[segmented="true"] QPushButton:checked {{ background: {c['selected']};
    color: {c['on_selected']}; }}
QFrame[segmented="true"] QPushButton[segment="left"] {{ border-top-left-radius: 17px;
    border-bottom-left-radius: 17px; }}
QFrame[segmented="true"] QPushButton[segment="right"] {{ border-top-right-radius: 17px;
    border-bottom-right-radius: 17px; }}
QFrame[segmented="true"] QPushButton:focus {{ border: 2px solid {c['focus']}; }}
QFrame#ActivitySwitch {{ border-radius: 15px; }}
QFrame#ActivitySwitch QPushButton {{ min-height: 28px; max-height: 28px; min-width: 44px;
    padding: 0 12px; font-size: 9pt; }}
QFrame#ActivitySwitch QPushButton[segment="left"] {{ border-top-left-radius: 14px;
    border-bottom-left-radius: 14px; }}
QFrame#ActivitySwitch QPushButton[segment="right"] {{ border-top-right-radius: 14px;
    border-bottom-right-radius: 14px; }}
ToggleSwitch {{ background: transparent; }}

/* Cards: filled for content, outlined for the drop target */
QFrame#Card {{ background: {c['surface']}; border-radius: 12px; }}
QFrame#ActionCard {{ background: {c['container']}; border-radius: 12px; }}
QFrame#DropZone {{ background: transparent; border: 1px solid {c['rule']}; border-radius: 12px; }}
QFrame#DropZone[state="focus"] {{ border: 1px solid {c['accent']}; }}
QFrame#DropZone[state="drag"] {{ background: {c['accent_soft']}; border: 2px solid {c['accent']}; }}
QFrame#DropZone QPlainTextEdit, QFrame#DropZone QPlainTextEdit:hover,
QFrame#DropZone QPlainTextEdit:focus, QFrame#DropZone QPlainTextEdit:disabled {{
    background: transparent; border: none; padding: 2px 0; }}
QLabel#SectionTitle {{ font-size: 11pt; font-weight: 500; color: {c['text']}; }}
QLabel#SectionHint, QLabel#FieldHint {{ color: {c['muted']}; font-size: 9pt; }}
QLabel#FieldLabel {{ color: {c['muted']}; font-weight: 500; }}
QLabel#EmptyTitle {{ font-size: 12pt; font-weight: 500; color: {c['text']}; }}
QLabel#EmptyHint {{ color: {c['muted']}; font-size: 9pt; }}
QLabel#QueueSummary {{ color: {c['muted']}; background: transparent;
    border: 1px solid {c['outline']}; border-radius: 8px; padding: 1px 8px;
    font-size: 9pt; font-weight: 500; }}
QLabel#QueueSummary[state="warning"] {{ color: {c['warning']}; }}
QLabel#StatusLabel {{ font-size: 12.5pt; font-weight: 500; color: {c['text']}; }}
QLabel#StatusDetail {{ color: {c['muted']}; }}
QLabel#StatusDot {{ border-radius: 5px; background: {c['outline']}; }}
{state_rules(c, 'QLabel#StatusDot', 'background')}
QLabel#DependencyStatus {{ color: {c['text']}; }}
{state_rules(c, 'QLabel#DependencyStatus', 'color')}
QLabel#DependencyStatus[state="ready"] {{ color: {c['success']}; }}

QProgressBar {{ background: {c['selected']}; border: none; border-radius: 2px;
    min-height: 4px; max-height: 4px; }}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 2px; }}
QPlainTextEdit#LogOutput, QPlainTextEdit#LogOutput:hover, QPlainTextEdit#LogOutput:focus {{
    background: transparent; color: {c['text']}; border: none; border-radius: 0;
    padding: 2px 0; font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; }}
QListWidget#SessionList {{ background: transparent; border: none; outline: 0; }}

QTabWidget::pane {{ background: {c['bg']}; border: none; border-top: 1px solid {c['rule']}; }}
QDialog#HistoryDialog QTabWidget::pane {{ top: 8px; }}
QTabBar::tab {{ background: transparent; border: none; border-bottom: 3px solid transparent;
    color: {c['muted']}; font-weight: 500; min-height: 34px; padding: 3px 20px; }}
QTabBar::tab:hover {{ background: {_HOVER}; color: {c['text']}; }}
QTabBar::tab:selected {{ color: {c['accent']}; border-bottom: 3px solid {c['accent']}; }}
QLabel#CookieTip, QLabel#HistoryNote {{ color: {c['muted']}; }}
QLabel#DialogTitle {{ font-size: 17pt; font-weight: 400; color: {c['text']}; }}
QTableWidget {{ background: {c['surface']}; alternate-background-color: {c['container']};
    border: none; border-radius: 12px; gridline-color: {c['rule']};
    selection-background-color: {c['selected']}; selection-color: {c['on_selected']}; }}
QTableWidget::item {{ padding: 6px; }}
QTableWidget QHeaderView::section {{ background: {c['container']}; border: none;
    border-bottom: 1px solid {c['rule']}; color: {c['muted']}; font-weight: 500; padding: 8px; }}
QTextBrowser {{ padding: 10px; }}
QScrollBar:vertical, QScrollBar:horizontal {{ background: transparent; border: none; }}
QScrollBar:vertical {{ width: 10px; margin: 2px 0; }}
QScrollBar:horizontal {{ height: 10px; margin: 0 2px; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {c['rule']}; border: 2px solid transparent; border-radius: 5px;
    min-height: 32px; min-width: 32px; }}
QScrollBar::handle:hover {{ background: {c['outline']}; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; }}
"""
