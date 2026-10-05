from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, Iterable, List, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QProcess,
    QPropertyAnimation,
    QSettings,
    QSize,
    QThread,
    QTimer,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QIcon, QKeySequence, QShortcut, QTextCursor
from PySide6.QtNetwork import QTcpSocket
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QPlainTextEdit,
    QPushButton,
    QButtonGroup,
    QComboBox,
    QFrame,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QStackedWidget,
    QScrollArea,
    QSizeGrip,
    QDialog,
    QTextBrowser,
)

from core.config import DownloadOptions
from core.dependencies import resolve_dependency_paths
from core.history import DownloadHistory
from core.utils import open_in_file_manager
from ui.components import HistoryDialog
from ui.components.elided_label import ElidedLabel
from ui.components.session_list import SessionList
from ui.components.title_bar import CustomTitleBar
from ui.components.toggle_switch import ToggleSwitch
from ui.icons import dither_pixmap, icon_action, icon_pixmap, line_icon
from ui.skins import DEFAULT_SKIN, SKINS, STATE_MARKS, active_skin
from ui.styles import COLORS, apply_chrome, strip_native_frames
from ui.text import count
from ui.url_queue import (
    QueueAnalysis,
    QueueMergeResult,
    analyze_url_queue,
    merge_url_queue,
)

if TYPE_CHECKING:
    from core.async_manager import AsyncVideoDownloadWorker
    from core.downloader import VideoDownloadWorker


logger = logging.getLogger(__name__)

_MAX_URL_LIST_BYTES = 5 * 1024 * 1024
_APP_TITLE = "YTDLE"

# (label, yt-dlp output template). Settings store the index, so keep the order.
_TEMPLATE_PRESETS = (
    ("Title", "%(title).150s"),
    ("Uploader - Title", "%(uploader)s - %(title).150s"),
    ("Playlist folder / 001 - Title", "%(playlist_title)s/%(playlist_index)03d - %(title).150s"),
    ("Channel folder / Date - Title", "%(channel)s/%(upload_date)s - %(title).100s"),
)

# Cookie sources: (saved value, shown name). Saved values match older settings.
_COOKIE_SOURCES = (
    ("None", "No cookies"),
    ("Cookie File (Fallback)", "Cookie file (cookies.txt)"),
    ("brave", "Brave"),
    ("chrome", "Chrome"),
    ("chromium", "Chromium"),
    ("edge", "Edge"),
    ("firefox", "Firefox"),
    ("opera", "Opera"),
    ("safari", "Safari"),
    ("vivaldi", "Vivaldi"),
)

# Layout floor: the window never asks for more height than this, even on
# small or high-DPI screens; the content fits at it without overlap.
_MIN_WIDTH, _MIN_HEIGHT, _FLOOR_HEIGHT = 760, 560, 480

_PAGES = (
    ("Download", "Paste links and download (Ctrl+1)"),
    ("Options", "File names, FFmpeg, speed, and toolchain (Ctrl+2)"),
    ("Cookies", "Sign-in cookies for restricted videos (Ctrl+3)"),
)


def _short_version(text: str) -> str:
    """'ffmpeg version 7.1 Copyright …' -> '7.1'; other strings pass through."""
    words = text.split()
    if len(words) >= 3 and words[1] == "version":
        return words[2]
    return text


def _segmented(parent: QWidget, name: str, buttons: Iterable[QPushButton]) -> QFrame:
    """Join checkable buttons into one pill-shaped control."""
    frame = QFrame(parent)
    frame.setObjectName(name)
    frame.setProperty("segmented", True)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    buttons = list(buttons)
    for index, button in enumerate(buttons):
        button.setParent(frame)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if index == 0:
            button.setProperty("segment", "left")
        elif index == len(buttons) - 1:
            button.setProperty("segment", "right")
        layout.addWidget(button)
    return frame


def _field_label(text: str, parent: QWidget, tip: str = "") -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName("FieldLabel")
    if tip:
        label.setToolTip(tip)
    return label


def _card(parent: QWidget, title: str, hint: str = "") -> tuple[QFrame, QVBoxLayout]:
    card = QFrame(parent)
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 16)
    layout.setSpacing(10)
    heading = QVBoxLayout()
    heading.setSpacing(2)
    title_label = QLabel(title, card)
    title_label.setObjectName("SectionTitle")
    heading.addWidget(title_label)
    if hint:
        hint_label = QLabel(hint, card)
        hint_label.setObjectName("SectionHint")
        hint_label.setWordWrap(True)
        heading.addWidget(hint_label)
    layout.addLayout(heading)
    return card, layout


def _scroll_page(content: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(content)
    return area


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle(_APP_TITLE)

        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[VideoDownloadWorker] = None
        self._async_worker: Optional[AsyncVideoDownloadWorker] = None
        self._history = DownloadHistory()
        self._use_async = True  # Enable async download manager by default

        deps = resolve_dependency_paths()
        self._ffmpeg_path = deps["ffmpeg"]
        self._aria2c_path = deps["aria2c"]
        self._yt_dlp_version = deps["yt_dlp"]
        self._ffmpeg_available: bool = self._ffmpeg_path != "Not found"
        self._aria2c_available: bool = self._aria2c_path != "Not found"
        self._ffmpeg_version = deps.get("ffmpeg_version", "unknown")
        self._aria2c_version = deps.get("aria2c_version", "unknown")

        self._downloading_total: int = 0
        self._downloading_started: int = 0
        self._downloading_completed: int = 0
        self._downloading_active: int = 0
        self._progress_floor: int = 0
        self._paused = False
        self._drag_active = False
        self._network_state = "pending"
        self._headline: tuple[str, str] = ("Ready", "ready")
        self._queue_count = 0
        # (button, icon name, [word] for word skins, visible label or None)
        self._actions: list[tuple[QWidget, str, Optional[str], Optional[str]]] = []
        self._queue_cache_text: Optional[str] = None
        self._queue_cache_analysis: Optional[QueueAnalysis] = None
        self._last_toolchain_console_text: Optional[str] = None
        self._live_status_active = False
        self._controls_enabled = True
        self._dependency_processes: dict[str, tuple[QProcess, str]] = {}
        self._network_socket: Optional[QTcpSocket] = None
        self._network_timer = QTimer(self)
        self._network_timer.setSingleShot(True)
        self._network_timer.timeout.connect(self._on_network_timeout)
        self._settings_save_timer = QTimer(self)
        self._settings_save_timer.setSingleShot(True)
        self._settings_save_timer.setInterval(250)
        self._settings_save_timer.timeout.connect(self._save_settings_now)

        self.settings = QSettings("Merlin", "YTDLE_v2")

        self._init_ui()
        strip_native_frames(self)
        self._load_settings()
        self.setAcceptDrops(True)
        self._start_dependency_version_probes()

        if not self._ffmpeg_available:
            self._warn_ffmpeg()

    # ------------------------------------------------------------------ layout

    def _init_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 6, 10, 12)
        root.setSpacing(8)

        self.title_bar = CustomTitleBar(self)
        root.addWidget(self.title_bar)
        self._build_title_bar_controls()

        self.pages = QStackedWidget(self)
        self.pages.addWidget(self._build_download_page())
        self.pages.addWidget(_scroll_page(self._build_options_page()))
        self.pages.addWidget(_scroll_page(self._build_cookies_page()))
        root.addWidget(self.pages, 1)

        self.setCentralWidget(central)
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(14, 14)

        self.start_button.clicked.connect(self._start_downloads)
        self.cancel_button.clicked.connect(self._cancel_downloads)
        self.pause_button.clicked.connect(self._toggle_pause)
        self.skip_button.clicked.connect(self._skip_current)
        self.mp3_btn.clicked.connect(self._update_quality_options)
        self.mp4_btn.clicked.connect(self._update_quality_options)
        self.template_presets.currentIndexChanged.connect(self._apply_template_preset)
        self.template_line.textChanged.connect(self._save_settings)
        self.url_input.textChanged.connect(self._update_queue_summary)
        self.ffmpeg_input.textChanged.connect(self._save_settings)
        self.ffmpeg_mode.currentIndexChanged.connect(self._save_settings)
        self.playlist_checkbox.stateChanged.connect(self._save_settings)
        self.restrict_checkbox.stateChanged.connect(self._save_settings)
        self.async_checkbox.stateChanged.connect(self._save_settings)
        self.aria2c_checkbox.stateChanged.connect(self._save_settings)
        self.quality_combo.currentIndexChanged.connect(self._save_settings)
        self.quality_combo.currentIndexChanged.connect(self._refresh_plan_summary)
        self.dir_input.textChanged.connect(self._save_settings)
        self.dir_input.textChanged.connect(self._refresh_plan_summary)
        self.mp3_btn.toggled.connect(self._save_settings)
        self.mp4_btn.toggled.connect(self._save_settings)
        self.session_list.itemDoubleClicked.connect(self._reveal_session_item)

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._start_downloads)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self._focus_links)
        QShortcut(QKeySequence("Ctrl+Shift+V"), self, activated=self._paste_from_clipboard)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self._import_url_list)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self._show_history_dialog)
        QShortcut(QKeySequence("Esc"), self, activated=self._cancel_downloads)
        for index in range(len(_PAGES)):
            QShortcut(
                QKeySequence(f"Ctrl+{index + 1}"),
                self,
                activated=lambda page=index: self._show_page(page),
            )

        self.mp3_btn.setChecked(True)
        self._update_quality_options()
        self._refresh_dependency_status()
        self._apply_skin_presentation()
        self._update_queue_summary()
        self._set_controls_enabled(True)
        self._set_status("Ready", "ready")

        self._fit_to_screen(920, 640)
        self.url_input.setFocus(Qt.FocusReason.OtherFocusReason)

        self._check_network_status()

    def _build_title_bar_controls(self) -> None:
        nav = QFrame(self)
        nav.setObjectName("NavBar")
        nav.setFixedHeight(40)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(3, 3, 3, 3)
        nav_layout.setSpacing(2)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for index, (label, tip) in enumerate(_PAGES):
            button = QPushButton(label, nav)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setToolTip(tip)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(button, index)
            nav_layout.addWidget(button)
        self.nav_group.button(0).setChecked(True)
        self.nav_group.idClicked.connect(self._show_page)
        self.title_bar.add_leading(nav)

        self.network_label = QLabel("Checking…", self)
        self.network_label.setObjectName("NetworkLabel")
        self.network_label.setProperty("state", "pending")
        self.network_label.setAccessibleName("Network status")
        self.network_label.setToolTip("Internet connection status")
        self.title_bar.add_trailing(self.network_label)

        self.check_network_button = QPushButton(self)
        self.check_network_button.setObjectName("CheckNetworkButton")
        self.check_network_button.setToolTip("Check the internet connection again")
        icon_action(self.check_network_button, "network", "Check network connection")
        self.check_network_button.setProperty("quiet", True)
        self.check_network_button.clicked.connect(self._check_network_status)
        self._register_action(self.check_network_button, "network", "recheck")
        self.title_bar.add_trailing(self.check_network_button)

        self.history_button = QPushButton(self)
        self.history_button.setObjectName("HistoryButton")
        self.history_button.setToolTip("Download history and failed links (Ctrl+H)")
        icon_action(self.history_button, "history", "Download history")
        self.history_button.setProperty("quiet", True)
        self.history_button.clicked.connect(self._show_history_dialog)
        self._register_action(self.history_button, "history", "history")
        self.title_bar.add_trailing(self.history_button)

    def _build_download_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(10)

        # Links: one drop target that is also the editor.
        self.drop_zone = QFrame(page)
        self.drop_zone.setObjectName("DropZone")
        self.drop_zone.setProperty("state", "idle")
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setContentsMargins(16, 10, 10, 8)
        drop_layout.setSpacing(4)

        url_header = QHBoxLayout()
        url_header.setSpacing(6)
        url_label = QLabel("Links", page)
        url_label.setObjectName("SectionTitle")
        url_label.setToolTip("Paste one URL per line. You can also drag & drop links here.")
        url_header.addWidget(url_label, 0)
        self.queue_label = QLabel("0 links", page)
        self.queue_label.setObjectName("QueueSummary")
        self.queue_label.setToolTip("How many non-empty lines are queued")
        self.queue_label.setFixedHeight(22)
        url_header.addWidget(self.queue_label, 0, Qt.AlignmentFlag.AlignVCenter)
        url_header.addStretch(1)

        self.paste_button = QPushButton("Paste", page)
        self.paste_button.setObjectName("PasteButton")
        self.paste_button.setIcon(line_icon("paste"))
        self.paste_button.setIconSize(QSize(18, 18))
        self.paste_button.setToolTip("Add links from the clipboard (Ctrl+Shift+V)")
        self.paste_button.setAccessibleName("Paste links from clipboard")
        self.paste_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        self._register_action(self.paste_button, "paste", "paste", "Paste")
        url_header.addWidget(self.paste_button, 0)

        self.import_urls_button = QPushButton(page)
        self.import_urls_button.setObjectName("ImportUrlsButton")
        self.import_urls_button.setToolTip("Add links from a UTF-8 text file (Ctrl+O)")
        icon_action(self.import_urls_button, "import", "Import URL list")
        self.import_urls_button.setProperty("quiet", True)
        self.import_urls_button.clicked.connect(self._import_url_list)
        self._register_action(self.import_urls_button, "import", "import")
        url_header.addWidget(self.import_urls_button, 0)

        self.clean_urls_button = QPushButton(page)
        self.clean_urls_button.setObjectName("CleanUrlsButton")
        self.clean_urls_button.setToolTip("Remove duplicate, invalid, and comment lines")
        icon_action(self.clean_urls_button, "clean", "Clean URL queue")
        self.clean_urls_button.setProperty("quiet", True)
        self.clean_urls_button.clicked.connect(self._clean_url_queue)
        self.clean_urls_button.setEnabled(False)
        self._register_action(self.clean_urls_button, "clean", "clean")
        url_header.addWidget(self.clean_urls_button, 0)

        self.clear_urls_button = QPushButton(page)
        self.clear_urls_button.setObjectName("ClearUrlsButton")
        self.clear_urls_button.setToolTip("Clear the current URL queue")
        icon_action(self.clear_urls_button, "clear", "Clear URL queue")
        self.clear_urls_button.setProperty("quiet", True)
        self.clear_urls_button.clicked.connect(self._clear_urls)
        self._register_action(self.clear_urls_button, "clear", "clear")
        url_header.addWidget(self.clear_urls_button, 0)
        drop_layout.addLayout(url_header)

        editor = QGridLayout()
        editor.setContentsMargins(0, 0, 0, 0)
        self.url_input = QPlainTextEdit(page)
        self.url_input.setTabChangesFocus(True)
        self.url_input.setAccessibleName("Download URLs")
        self.url_input.setMinimumHeight(48)
        self.url_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        # Drops go to the window, so they are validated and de-duplicated.
        self.url_input.setAcceptDrops(False)
        self.url_input.installEventFilter(self)
        editor.addWidget(self.url_input, 0, 0)
        self.empty_state = self._build_empty_state(page)
        editor.addWidget(self.empty_state, 0, 0)
        drop_layout.addLayout(editor, 1)
        layout.addWidget(self.drop_zone, 3)
        self._download_layout = layout

        # What to download.
        choice_row = QHBoxLayout()
        choice_row.setSpacing(10)
        self.mp3_btn = QPushButton("MP3")
        self.mp3_btn.setObjectName("FormatSegmentLeft")
        self.mp3_btn.setProperty("formatToggle", True)
        self.mp3_btn.setIcon(line_icon("audio"))
        self.mp3_btn.setIconSize(QSize(18, 18))
        self.mp3_btn.setAccessibleName("MP3 audio")
        self.mp3_btn.setToolTip(
            "Audio only. Converts the best audio to MP3 at the selected bitrate."
        )
        self.mp4_btn = QPushButton("MP4")
        self.mp4_btn.setObjectName("FormatSegmentRight")
        self.mp4_btn.setProperty("formatToggle", True)
        self.mp4_btn.setIcon(line_icon("video"))
        self.mp4_btn.setIconSize(QSize(18, 18))
        self.mp4_btn.setAccessibleName("MP4 video")
        self.mp4_btn.setToolTip("Video (MP4). Respects the maximum resolution you select.")
        self.format_switch = _segmented(page, "FormatSwitch", (self.mp3_btn, self.mp4_btn))
        self._register_action(self.mp3_btn, "audio", None, "MP3")
        self._register_action(self.mp4_btn, "video", None, "MP4")
        self.fmt_group = QButtonGroup(self)
        self.fmt_group.setExclusive(True)
        self.fmt_group.addButton(self.mp3_btn)
        self.fmt_group.addButton(self.mp4_btn)
        choice_row.addWidget(self.format_switch, 0)

        self.quality_combo = QComboBox(page)
        self.quality_combo.setAccessibleName("Quality")
        self.quality_combo.setMinimumWidth(104)
        self.quality_combo.setToolTip(
            "MP3: bitrate (kbps). MP4: maximum video resolution. 'Best' picks the highest available."
        )
        choice_row.addWidget(self.quality_combo, 0)
        choice_row.addSpacing(4)

        self.playlist_checkbox = ToggleSwitch("Whole playlist", page)
        self.playlist_checkbox.setToolTip(
            "If the link is a playlist or series, download every item. Otherwise only the single video."
        )
        choice_row.addWidget(self.playlist_checkbox, 0)
        choice_row.addStretch(1)
        layout.addLayout(choice_row)

        # Where it goes.
        dir_row = QHBoxLayout()
        dir_row.setSpacing(6)
        dir_row.addWidget(_field_label("Save to", page, "Folder where files will be saved."), 0)
        self.dir_input = QLineEdit(page)
        self.dir_input.setPlaceholderText("Download folder")
        self.dir_input.setAccessibleName("Download folder")
        self.dir_input.setToolTip("Folder where files will be saved.")
        self.dir_input.setMaxLength(1024)
        dir_row.addWidget(self.dir_input, 1)

        self.browse_button = QToolButton(page)
        self.browse_button.setObjectName("BrowseButton")
        self.browse_button.setIcon(line_icon("folder"))
        self.browse_button.setToolTip("Choose download folder")
        self.browse_button.setAccessibleName("Choose download directory")
        self.browse_button.clicked.connect(self._choose_directory)
        self._register_action(self.browse_button, "folder", "browse")
        dir_row.addWidget(self.browse_button, 0)

        self.open_folder_button = QToolButton(page)
        self.open_folder_button.setObjectName("OpenFolderButton")
        self.open_folder_button.setIcon(line_icon("launch"))
        self.open_folder_button.setToolTip("Open the download folder in your file manager")
        self.open_folder_button.setAccessibleName("Open current download folder")
        self.open_folder_button.clicked.connect(self._open_folder)
        self._register_action(self.open_folder_button, "launch", "open")
        dir_row.addWidget(self.open_folder_button, 0)
        layout.addLayout(dir_row)

        layout.addWidget(self._build_action_card(page))
        self._activity_card = self._build_activity_panel(page)
        layout.addWidget(self._activity_card, 2)
        return page

    def _build_empty_state(self, parent: QWidget) -> QWidget:
        panel = QWidget(parent)
        panel.setObjectName("EmptyState")
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)
        icon = QLabel(panel)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_art = icon
        title = QLabel("Drop or paste links here", panel)
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel(
            "YouTube, TikTok, X, SoundCloud and many more · one link per line\n"
            "Ctrl+Shift+V pastes · Ctrl+O imports a list",
            panel,
        )
        hint.setObjectName("EmptyHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for widget in (icon, title, hint):
            layout.addWidget(widget)
        # Clicks fall through to the editor underneath.
        for widget in (panel, icon, title, hint):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        return panel

    def _build_action_card(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("ActionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 12, 12, 12)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.status_dot = QLabel(card)
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setProperty("state", "ready")
        top.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addSpacing(4)

        text = QVBoxLayout()
        text.setSpacing(1)
        self.status_label = ElidedLabel("Ready", card)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setProperty("state", "ready")
        self.status_label.setAccessibleName("Download status")
        # Middle elision keeps both the link count and the folder name visible.
        self.status_detail = ElidedLabel("", card, elide=Qt.TextElideMode.ElideMiddle)
        self.status_detail.setObjectName("StatusDetail")
        self.status_detail.setAccessibleName("Download details")
        text.addWidget(self.status_label)
        text.addWidget(self.status_detail)
        top.addLayout(text, 1)

        self.pause_button = QPushButton(card)
        self.pause_button.setObjectName("PauseButton")
        self.pause_button.setToolTip("Pause downloads")
        icon_action(self.pause_button, "pause", "Pause download")
        self.skip_button = QPushButton(card)
        self.skip_button.setObjectName("SkipButton")
        self.skip_button.setToolTip("Skip the current download and move to the next")
        icon_action(self.skip_button, "skip", "Skip current download")
        self._register_action(self.skip_button, "skip", "skip")
        self.cancel_button = QPushButton("Stop", card)
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setIcon(line_icon("cancel"))
        self.cancel_button.setIconSize(QSize(18, 18))
        self.cancel_button.setAccessibleName("Cancel downloads")
        self.cancel_button.setToolTip("Stop after the current files finish processing (Esc)")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._register_action(self.cancel_button, "cancel", "stop", "Stop")
        self.start_button = QPushButton("Download", card)
        self.start_button.setObjectName("DownloadButton")
        self.start_button.setIconSize(QSize(20, 20))
        self.start_button.setAccessibleName("Start download")
        self.start_button.setToolTip("Download every link in the list (Ctrl+Enter)")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        for button in (self.pause_button, self.skip_button, self.cancel_button, self.start_button):
            top.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(top)

        self.progress_bar = QProgressBar(card)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("Download progress")
        layout.addWidget(self.progress_bar)
        self._progress_animation = QPropertyAnimation(self.progress_bar, b"value", self)
        self._progress_animation.setDuration(240)
        self._progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return card

    def _build_activity_panel(self, parent: QWidget) -> QFrame:
        card = QFrame(parent)
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("Activity", card)
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.activity_items_button = QPushButton("Downloads")
        self.activity_items_button.setToolTip("One row per link in this session")
        self.activity_log_button = QPushButton("Log")
        self.activity_log_button.setToolTip("Toolchain, network, and yt-dlp output")
        switch = _segmented(
            card, "ActivitySwitch", (self.activity_items_button, self.activity_log_button)
        )
        self.activity_group = QButtonGroup(self)
        self.activity_group.setExclusive(True)
        self.activity_group.addButton(self.activity_items_button, 0)
        self.activity_group.addButton(self.activity_log_button, 1)
        header.addWidget(switch)
        layout.addLayout(header)

        self.activity_stack = QStackedWidget(card)
        self.session_list = SessionList(card)
        self.session_list.setMinimumHeight(44)
        self.activity_stack.addWidget(self.session_list)

        self.log_output = QPlainTextEdit(card)
        self.log_output.setObjectName("LogOutput")
        self.log_output.setReadOnly(True)
        # UI history is a view, not the persistent log: bound its document size.
        self.log_output.document().setMaximumBlockCount(1500)
        self.log_output.setAccessibleName("Download activity log")
        self.log_output.setMinimumHeight(44)
        self.log_output.setPlaceholderText("Status and activity will appear here.")
        self.activity_stack.addWidget(self.log_output)
        layout.addWidget(self.activity_stack, 1)

        self.activity_group.idClicked.connect(self.activity_stack.setCurrentIndex)
        self.activity_items_button.setChecked(True)
        return card

    def _build_options_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(10)

        skin_card, skin_layout = _card(page, "Skin", "How YTDLE looks. Your pick is saved for next time.")
        self._skin_keys = list(SKINS)
        skin_buttons = [QPushButton(SKINS[key].name) for key in self._skin_keys]
        self.skin_switch = _segmented(page, "SkinSwitch", skin_buttons)
        self.skin_group = QButtonGroup(self)
        self.skin_group.setExclusive(True)
        for index, (key, button) in enumerate(zip(self._skin_keys, skin_buttons)):
            button.setAccessibleName(f"{SKINS[key].name} skin")
            button.setToolTip(SKINS[key].summary)
            self.skin_group.addButton(button, index)
        self.skin_group.idClicked.connect(lambda index: self._apply_skin(self._skin_keys[index]))
        skin_row = QHBoxLayout()
        skin_row.addWidget(self.skin_switch, 0)
        skin_row.addStretch(1)
        skin_layout.addLayout(skin_row)
        self.skin_summary = QLabel("", page)
        self.skin_summary.setObjectName("SectionHint")
        self.skin_summary.setWordWrap(True)
        skin_layout.addWidget(self.skin_summary)
        layout.addWidget(skin_card)

        naming, naming_layout = _card(
            page, "File names", "How saved files and folders are named. The extension is added for you."
        )
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_row.addWidget(_field_label("Preset", page), 0)
        self.template_presets = QComboBox(page)
        self.template_presets.setAccessibleName("File name preset")
        for label, template in _TEMPLATE_PRESETS:
            self.template_presets.addItem(label, template)
            self.template_presets.setItemData(
                self.template_presets.count() - 1, template, Qt.ItemDataRole.ToolTipRole
            )
        self.template_presets.setToolTip("Pick a common naming pattern for file names and folders.")
        preset_row.addWidget(self.template_presets, 1)
        naming_layout.addLayout(preset_row)

        template_row = QHBoxLayout()
        template_row.setSpacing(8)
        template_row.addWidget(_field_label("Template", page), 0)
        self.template_line = QLineEdit(page)
        self.template_line.setAccessibleName("Output template")
        self.template_line.setPlaceholderText("%(title).150s")
        self.template_line.setMaxLength(512)
        self.template_line.setToolTip(
            "Freeform yt-dlp output template (no extension). Example: %(uploader)s - %(title).150s"
        )
        template_row.addWidget(self.template_line, 1)
        naming_layout.addLayout(template_row)

        self.restrict_checkbox = ToggleSwitch("Safe file names (ASCII only)", page)
        self.restrict_checkbox.setToolTip(
            "Use only ASCII-safe characters in file names (helps on some filesystems)."
        )
        naming_layout.addWidget(self.restrict_checkbox)
        layout.addWidget(naming)

        post, post_layout = _card(
            page,
            "FFmpeg arguments",
            "Optional. Append adds to YTDLE's defaults; Override replaces them.",
        )
        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.setSpacing(8)
        self.ffmpeg_input = QLineEdit(page)
        self.ffmpeg_input.setAccessibleName("Custom FFmpeg arguments")
        self.ffmpeg_input.setPlaceholderText("e.g. -vcodec libx264")
        self.ffmpeg_input.setMaxLength(2048)
        self.ffmpeg_input.setToolTip("Pass extra arguments to the FFmpeg post-processor.")
        ffmpeg_row.addWidget(self.ffmpeg_input, 1)
        self.ffmpeg_mode = QComboBox(page)
        self.ffmpeg_mode.setAccessibleName("FFmpeg argument mode")
        self.ffmpeg_mode.addItems(["Append", "Override"])
        self.ffmpeg_mode.setToolTip("Append: add to defaults. Override: replace or force specific args.")
        self.ffmpeg_mode.setFixedWidth(120)
        ffmpeg_row.addWidget(self.ffmpeg_mode, 0)
        post_layout.addLayout(ffmpeg_row)
        layout.addWidget(post)

        speed, speed_layout = _card(page, "Speed", "Up to 3 links download at the same time.")
        self.async_checkbox = ToggleSwitch("Parallel downloads", page)
        self.async_checkbox.setToolTip(
            "Use the async download manager for better concurrency and performance."
        )
        self.async_checkbox.setChecked(True)
        self.aria2c_checkbox = ToggleSwitch("Multi-connection downloads (aria2c)", page)
        self.aria2c_checkbox.setToolTip(
            "Use aria2c for multi-connection downloads (faster, needs the aria2c binary)."
        )
        speed_layout.addWidget(self.async_checkbox)
        speed_layout.addWidget(self.aria2c_checkbox)
        layout.addWidget(speed)

        tools, tools_layout = _card(page, "Toolchain", "Programs YTDLE uses to download and convert.")
        self.dependency_label = QLabel("Checking tools...", page)
        self.dependency_label.setObjectName("DependencyStatus")
        self.dependency_label.setProperty("state", "pending")
        self.dependency_label.setAccessibleName("Toolchain status")
        self.dependency_label.setWordWrap(True)
        self.dependency_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        tools_layout.addWidget(self.dependency_label)
        layout.addWidget(tools)
        layout.addStretch(1)
        return page

    def _build_cookies_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 8)
        layout.setSpacing(10)

        source, source_layout = _card(
            page,
            "Cookie source",
            "Cookies let YTDLE download age-restricted or members-only videos you can already watch. "
            "Exactly one source is used.",
        )
        browser_row = QHBoxLayout()
        browser_row.setSpacing(8)
        browser_row.addWidget(_field_label("Source", page), 0)
        self.browser_combo = QComboBox(page)
        self.browser_combo.setAccessibleName("Cookie source")
        for value, shown in _COOKIE_SOURCES:
            self.browser_combo.addItem(shown, value)
        self.browser_combo.setToolTip(
            "Cookie source. Exactly one source is used:\n"
            "- No cookies: send none.\n"
            "- Cookie file: use the cookies.txt file below exclusively.\n"
            "- A browser: read cookies from that browser only.\n"
            "For Chromium forks (Thorium, Ungoogled, etc.), use a cookie file."
        )
        self.browser_combo.currentIndexChanged.connect(
            lambda _index: self._on_browser_changed(self._cookie_source())
        )
        browser_row.addWidget(self.browser_combo, 1)
        self.help_button = QToolButton(page)
        self.help_button.setObjectName("HelpButton")
        self.help_button.setIcon(line_icon("help"))
        self.help_button.setIconSize(QSize(18, 18))
        self.help_button.setToolTip("Open the cookie guide")
        self.help_button.setAccessibleName("Open Cookie Help Guide")
        self.help_button.clicked.connect(self._show_cookie_help)
        self._register_action(self.help_button, "help", "help")
        browser_row.addWidget(self.help_button, 0)
        source_layout.addLayout(browser_row)

        browser_fields = QGridLayout()
        browser_fields.setHorizontalSpacing(8)
        browser_fields.setVerticalSpacing(8)
        self.profile_input = QLineEdit(page)
        self.profile_input.setAccessibleName("Browser profile")
        self.profile_input.setPlaceholderText("Default profile (e.g. 'Profile 1')")
        self.profile_input.setToolTip("Specify a browser profile if you have more than one.")
        self.profile_input.textChanged.connect(self._save_settings)
        self.profile_input.setMaxLength(256)
        self.keyring_input = QLineEdit(page)
        self.keyring_input.setAccessibleName("Keyring backend")
        self.keyring_input.setPlaceholderText("Linux only, usually empty")
        self.keyring_input.setToolTip("For Linux systems with custom keyring configurations.")
        self.keyring_input.textChanged.connect(self._save_settings)
        self.keyring_input.setMaxLength(64)
        self.container_input = QLineEdit(page)
        self.container_input.setAccessibleName("Firefox container")
        self.container_input.setPlaceholderText("Firefox container (e.g. 'Work')")
        self.container_input.setToolTip("Firefox Multi-Account Container name (e.g. 'Personal', 'Work').")
        self.container_input.textChanged.connect(self._save_settings)
        self.container_input.setMaxLength(256)
        browser_fields.addWidget(_field_label("Profile", page), 0, 0)
        browser_fields.addWidget(self.profile_input, 0, 1, 1, 3)
        if sys.platform.startswith("linux"):
            # Keyring backends exist only on Linux; elsewhere the field cannot be used.
            browser_fields.addWidget(_field_label("Keyring", page), 1, 0)
            browser_fields.addWidget(self.keyring_input, 1, 1)
            browser_fields.addWidget(_field_label("Container", page), 1, 2)
            browser_fields.addWidget(self.container_input, 1, 3)
        else:
            self.keyring_input.hide()
            browser_fields.addWidget(_field_label("Container", page), 1, 0)
            browser_fields.addWidget(self.container_input, 1, 1, 1, 3)
        browser_fields.setColumnStretch(1, 1)
        browser_fields.setColumnStretch(3, 1)
        source_layout.addLayout(browser_fields)
        layout.addWidget(source)

        file_card, file_layout = _card(
            page,
            "Cookie file",
            "A Netscape-format cookies.txt. Used only when the source is 'Cookie file'.",
        )
        file_row = QHBoxLayout()
        file_row.setSpacing(6)
        self.cookie_file_input = QLineEdit(page)
        self.cookie_file_input.setAccessibleName("Cookie file path")
        self.cookie_file_input.setPlaceholderText("Path to cookies.txt")
        self.cookie_file_input.setToolTip(
            "Netscape-format cookie file exported from a browser. "
            "Used exclusively when 'Cookie file' is selected above."
        )
        self.cookie_file_input.textChanged.connect(self._save_settings)
        self.cookie_file_input.setMaxLength(1024)
        self.cookie_file_browse = QToolButton(page)
        self.cookie_file_browse.setObjectName("CookieBrowseButton")
        self.cookie_file_browse.setIcon(line_icon("file"))
        self.cookie_file_browse.setToolTip("Browse for cookie file")
        self.cookie_file_browse.setAccessibleName("Browse for cookie file")
        self.cookie_file_browse.clicked.connect(self._choose_cookie_file)
        self._register_action(self.cookie_file_browse, "file", "browse")
        file_row.addWidget(self.cookie_file_input, 1)
        file_row.addWidget(self.cookie_file_browse, 0)
        file_layout.addLayout(file_row)
        layout.addWidget(file_card)

        info_label = QLabel(
            "Tip: close the browser before downloading, so its cookie database is not locked.",
            page,
        )
        info_label.setObjectName("CookieTip")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        layout.addStretch(1)
        return page

    # ------------------------------------------------------------------ skins

    def _register_action(
        self, button: QWidget, icon: str, word: Optional[str], label: Optional[str] = None
    ) -> None:
        """Remember how an action reads: an icon (and label) or a [word]."""
        self._actions.append((button, icon, word, label))

    def _apply_skin(self, key: str, *, save: bool = True) -> None:
        """Switch the look now, without rebuilding the window."""
        app = QApplication.instance()
        if app is not None and (key != active_skin().key or save):
            apply_chrome(app, key)
        self._apply_skin_presentation()
        if save:
            self.settings.setValue("skin", active_skin().key)

    def _apply_skin_presentation(self) -> None:
        """Everything a stylesheet cannot change: icons or words, marks, art, pixmaps."""
        skin = active_skin()
        self.title_bar.refresh_skin()
        for button, icon, word, label in self._actions:
            if skin.icon_actions or word is None:
                button.setIcon(line_icon(icon) if skin.icon_actions else QIcon())
                button.setText(label or "")
            else:
                button.setIcon(QIcon())
                button.setText(f"[{word}]")
            if isinstance(button, QToolButton):
                button.setToolButtonStyle(
                    Qt.ToolButtonStyle.ToolButtonIconOnly
                    if skin.icon_actions
                    else Qt.ToolButtonStyle.ToolButtonTextOnly
                )
        self.start_button.setIcon(
            QIcon(icon_pixmap("download", 20, COLORS["on_accent"])) if skin.icon_actions else QIcon()
        )
        self._set_pause_button(paused=self._paused)
        self._refresh_start_label()
        for button in self.nav_group.buttons():
            label = _PAGES[self.nav_group.id(button)][0]
            if skin.page_marker:
                label = ("> " if button.isChecked() else "  ") + label
            button.setText(label)
        if skin.empty_art == "dither":
            self.empty_art.setPixmap(dither_pixmap("download", 120, 72, COLORS["art_ink"]))
        else:
            self.empty_art.setPixmap(icon_pixmap("link", 28, COLORS["focus"]))
        self.status_dot.setVisible(not skin.state_marks)
        self._render_headline(*self._headline)
        self._render_network()
        for toggle in self.findChildren(ToggleSwitch):
            toggle.updateGeometry()
            toggle.update()
        self.session_list.viewport().update()
        position = self._skin_keys.index(skin.key)
        self.skin_group.button(position).setChecked(True)
        self.skin_summary.setText(skin.summary)

    def _render_headline(self, text: str, state: str) -> None:
        """Headline in the action card; word skins prefix [ok] / [!] / ... marks."""
        self._headline = (text, state)
        mark = STATE_MARKS.get(state) if active_skin().state_marks else None
        self.status_label.setText(f"{mark} {text}" if mark else text)
        self._set_widget_state(self.status_label, state)
        self._set_widget_state(self.status_dot, state)

    def _render_network(self) -> None:
        state = self._network_state
        if active_skin().state_marks:
            text = {"online": "[online]", "offline": "[offline]"}.get(state, "[checking]")
        else:
            text = {"online": "● Online", "offline": "● Offline"}.get(state, "Checking…")
        self.network_label.setText(text)
        visual = {"online": "done", "offline": "error"}.get(state, "pending")
        self._set_widget_state(self.network_label, visual)

    def _refresh_start_label(self) -> None:
        label = "Download" if self._queue_count <= 1 else f"Download {count(self._queue_count)}"
        if not active_skin().icon_actions:
            label = f"[{label.lower()}]"
        self.start_button.setText(label)

    def _set_activity_priority(self, focused: bool) -> None:
        """While a batch runs (and after), the per-link rows get the room."""
        self._download_layout.setStretchFactor(self.drop_zone, 1 if focused else 3)
        self._download_layout.setStretchFactor(self._activity_card, 3 if focused else 2)

    def _fit_to_screen(self, width: int, height: int) -> None:
        """Size the window for its screen; small or high-DPI screens lower the minimum."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        min_height = _MIN_HEIGHT
        if available is not None:
            min_height = max(_FLOOR_HEIGHT, min(_MIN_HEIGHT, available.height()))
            width = min(width, available.width())
            height = min(height, available.height())
        self.setMinimumSize(_MIN_WIDTH, min_height)
        self.resize(max(width, _MIN_WIDTH), max(height, min_height))

    # ---------------------------------------------------------- window chrome

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        grip = getattr(self, "_size_grip", None)
        if grip is not None:
            grip.move(self.width() - grip.width(), self.height() - grip.height())
            grip.raise_()

    def eventFilter(self, watched, event) -> bool:
        if watched is getattr(self, "url_input", None) and event.type() in (
            QEvent.Type.FocusIn,
            QEvent.Type.FocusOut,
        ):
            self._sync_drop_zone_state()
        return super().eventFilter(watched, event)

    def _sync_drop_zone_state(self) -> None:
        if self._drag_active:
            state = "drag"
        elif self.url_input.hasFocus():
            state = "focus"
        elif self.url_input.document().isEmpty():
            state = "idle"
        else:
            state = "filled"
        self._set_widget_state(self.drop_zone, state)

    def _show_page(self, index: int) -> None:
        button = self.nav_group.button(index)
        if button is not None:
            button.setChecked(True)
        self.pages.setCurrentIndex(index)
        if active_skin().page_marker:
            for other in self.nav_group.buttons():
                label = _PAGES[self.nav_group.id(other)][0]
                other.setText(("> " if other.isChecked() else "  ") + label)

    def _focus_links(self) -> None:
        self._show_page(0)
        self.url_input.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        self._show_page(0)
        if not text.strip():
            self._set_status("The clipboard has no text to add.", "warning")
            return
        self._add_urls_to_queue((text,), "the clipboard")

    @staticmethod
    def _set_widget_state(widget: QWidget, state: str) -> None:
        """Refresh a dynamic QSS state only when its semantic value changes."""
        if widget.property("state") == state:
            return
        widget.setProperty("state", state)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _set_status(
        self,
        message: str,
        state: str = "ready",
        *,
        live: bool = False,
    ) -> None:
        """Show a status in the action card and record it in the activity log.

        The first line is the headline; any further lines become the detail.
        """
        headline, _, detail = message.partition("\n")
        self._render_headline(headline, state)
        if detail:
            self.status_detail.setText(detail.replace("\n", " "))
        if live:
            self._set_live_console_status(f"Status: {message}")
        else:
            self.append_log(f"Status: {message}")

    def _refresh_plan_summary(self) -> None:
        """Say what Download will do, before the user commits to it."""
        if not self._controls_enabled:
            return
        links = len(self._get_queue_analysis().urls)
        kind = "MP3" if self.mp3_btn.isChecked() else "MP4"
        target = self.dir_input.text().strip() or "no folder chosen"
        if links:
            noun = "link" if links == 1 else "links"
            lead = f"{count(links)} {noun}"
        else:
            lead = "Add links to start"
        self.status_detail.setText(
            f"{lead} · {kind} {self.quality_combo.currentText()} · to {target}"
        )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            self._drag_active = True
            self._show_page(0)
            self._sync_drop_zone_state()
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event) -> None:
        self._drag_active = False
        self._sync_drop_zone_state()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._drag_active = False
        self._sync_drop_zone_state()
        text_parts: List[str] = []
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isValid():
                    text_parts.append(url.toString())
        if not text_parts and event.mimeData().hasText():
            txt = event.mimeData().text()
            if txt:
                text_parts.append(txt)
        if text_parts:
            self._add_urls_to_queue(text_parts, "drag and drop")
        event.acceptProposedAction()

    def _import_url_list(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import URL List",
            "",
            "URL Lists (*.txt *.list);;All Files (*)",
        )
        if not file_path:
            return

        file_name = os.path.basename(file_path) or "selected file"
        try:
            file_size = os.path.getsize(file_path)
            if file_size > _MAX_URL_LIST_BYTES:
                QMessageBox.warning(
                    self,
                    "List Too Large",
                    "The selected list is larger than 5 MB. "
                    "Split it into smaller files before importing.",
                )
                return
            with open(file_path, "r", encoding="utf-8-sig") as url_file:
                contents = url_file.read()
        except UnicodeError as error:
            self.append_log(f"Could not import {file_name}: {error}")
            QMessageBox.warning(
                self,
                "Cannot Read List",
                f"YTDLE could not read {file_name}. Save it as UTF-8 text and try again.",
            )
            return
        except OSError as error:
            self.append_log(f"Could not import {file_name}: {error}")
            QMessageBox.warning(
                self,
                "Cannot Open List",
                f"YTDLE could not open {file_name}. Check the file and your permissions, then try again.",
            )
            return

        self._add_urls_to_queue((contents,), file_name)

    def _add_urls_to_queue(
        self,
        incoming_texts: Iterable[str],
        source: str,
    ) -> QueueMergeResult:
        existing_text = self.url_input.toPlainText()
        result = merge_url_queue(
            existing_text,
            incoming_texts,
            existing_analysis=self._get_queue_analysis(existing_text),
        )
        if result.added_count:
            self.url_input.setPlainText(result.text)
        else:
            self._update_queue_summary()

        message = self._queue_change_message(result, source)
        self._set_status(message, "ready")
        return result

    @staticmethod
    def _queue_change_message(result: QueueMergeResult, source: str) -> str:
        if result.added_count:
            noun = "link" if result.added_count == 1 else "links"
            action = f"Added {result.added_count} {noun} from {source}."
        elif result.duplicate_count or result.invalid_entries:
            action = f"No new links added from {source}."
        else:
            return f"No links found in {source}."

        skipped: list[str] = []
        if result.duplicate_count:
            noun = "duplicate" if result.duplicate_count == 1 else "duplicates"
            skipped.append(f"{result.duplicate_count} {noun}")
        invalid_count = len(result.invalid_entries)
        if invalid_count:
            noun = "invalid entry" if invalid_count == 1 else "invalid entries"
            skipped.append(f"{invalid_count} {noun}")

        if skipped:
            action += f" Skipped {' and '.join(skipped)}."
        return action

    def _default_download_dir(self) -> str:
        root_dir = os.path.expanduser("~")
        return os.path.join(root_dir, "YTDLE")

    def _load_settings(self) -> None:
        directory = self.settings.value(
            "directory", self._default_download_dir(), type=str
        )
        self.dir_input.setText(directory)

        last_is_mp3 = self.settings.value("is_mp3", True, type=bool)
        self.mp3_btn.setChecked(bool(last_is_mp3))
        self.mp4_btn.setChecked(not bool(last_is_mp3))
        self._update_quality_options()

        last_quality = self.settings.value("quality", None, type=str)
        if last_quality:
            index = self.quality_combo.findText(last_quality)
            if index >= 0:
                self.quality_combo.setCurrentIndex(index)

        playlist = self.settings.value("download_playlist", False, type=bool)
        restrict = self.settings.value("restrict_filenames", False, type=bool)
        use_async = self.settings.value("use_async", True, type=bool)
        use_aria2c = self.settings.value("use_aria2c", False, type=bool)
        self.playlist_checkbox.setChecked(bool(playlist))
        self.restrict_checkbox.setChecked(bool(restrict))
        self.async_checkbox.setChecked(bool(use_async))
        self.aria2c_checkbox.setChecked(bool(use_aria2c))

        preset_index = self.settings.value("template_preset_index", 0, type=int)
        if 0 <= preset_index < self.template_presets.count():
            self.template_presets.setCurrentIndex(preset_index)
        template = self.settings.value("outtmpl_template", "%(title).150s", type=str)
        self.template_line.setText(template)

        ffmpeg_args = self.settings.value("ffmpeg_args", "", type=str)
        self.ffmpeg_input.setText(ffmpeg_args)

        ffmpeg_mode = self.settings.value("ffmpeg_mode", "Append", type=str)
        idx = self.ffmpeg_mode.findText(ffmpeg_mode)
        if idx >= 0:
            self.ffmpeg_mode.setCurrentIndex(idx)

        # Cookie settings
        cookie_file = self.settings.value("cookie_file", "", type=str).strip()
        browser = self.settings.value("cookie_browser", "None", type=str)
        if self.browser_combo.findData(browser) < 0:
            browser = "None"
        # Legacy configs saved a cookie file while the source was 'None' and the
        # file was still sent. Keep those downloads working: switch to the file source.
        if browser == "None" and cookie_file:
            browser = self.COOKIE_FILE_SOURCE
        self._select_cookie_source(browser)

        self.profile_input.setText(self.settings.value("cookie_profile", "", type=str))
        self.keyring_input.setText(self.settings.value("cookie_keyring", "", type=str))
        self.container_input.setText(
            self.settings.value("cookie_container", "", type=str)
        )
        self.cookie_file_input.setText(cookie_file)
        self._update_browser_fields(self._cookie_source())

        skin = self.settings.value("skin", DEFAULT_SKIN, type=str)
        if skin != active_skin().key:
            self._apply_skin(skin, save=False)

    def _save_settings(self) -> None:
        """Coalesce rapid control edits so typing never performs disk work."""
        self._settings_save_timer.start()

    def _save_settings_now(self) -> None:
        self.settings.setValue("directory", self.dir_input.text().strip())
        is_mp3 = self.mp3_btn.isChecked()
        self.settings.setValue("is_mp3", is_mp3)
        self.settings.setValue("quality", self.quality_combo.currentText())
        self.settings.setValue("download_playlist", self.playlist_checkbox.isChecked())
        self.settings.setValue("restrict_filenames", self.restrict_checkbox.isChecked())
        self.settings.setValue("use_async", self.async_checkbox.isChecked())
        self.settings.setValue("use_aria2c", self.aria2c_checkbox.isChecked())
        self.settings.setValue(
            "template_preset_index", self.template_presets.currentIndex()
        )
        self.settings.setValue("outtmpl_template", self.template_line.text())
        self.settings.setValue("ffmpeg_args", self.ffmpeg_input.text())
        self.settings.setValue("ffmpeg_mode", self.ffmpeg_mode.currentText())

        # Cookie settings
        self.settings.setValue("cookie_browser", self._cookie_source())
        self.settings.setValue("cookie_profile", self.profile_input.text())
        self.settings.setValue("cookie_keyring", self.keyring_input.text())
        self.settings.setValue("cookie_container", self.container_input.text())
        self.settings.setValue("cookie_file", self.cookie_file_input.text())

    def _apply_template_preset(self) -> None:
        # Only replace a template the user has not customized.
        current = self.template_line.text().strip()
        if not current or current in (template for _label, template in _TEMPLATE_PRESETS):
            self.template_line.setText(self.template_presets.currentData())
        self._save_settings()

    def _update_quality_options(self) -> None:
        self.quality_combo.clear()
        if self.mp3_btn.isChecked():
            self.quality_combo.addItems(["320k", "256k", "192k", "128k"])
        else:
            self.quality_combo.addItems(
                ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
            )
        self._save_settings()

    def _choose_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.dir_input.text()
        )
        if path:
            self.dir_input.setText(os.path.normpath(path))

    def _open_folder(self) -> None:
        open_in_file_manager(self.dir_input.text().strip())

    def _get_queue_analysis(self, text: Optional[str] = None) -> QueueAnalysis:
        """Return analysis for the editor's exact current text without stale reuse."""
        if text is None:
            text = self.url_input.toPlainText()
        if text != self._queue_cache_text or self._queue_cache_analysis is None:
            self._queue_cache_text = text
            self._queue_cache_analysis = analyze_url_queue(text)
        return self._queue_cache_analysis

    def _clean_url_queue(self) -> None:
        analysis = self._get_queue_analysis()
        if not analysis.has_cleanup_items:
            self._set_status("Queue is already clean.", "ready")
            return

        self.url_input.setPlainText(analysis.cleaned_text)
        removed: list[str] = []
        if analysis.duplicate_count:
            noun = "duplicate" if analysis.duplicate_count == 1 else "duplicates"
            removed.append(f"{analysis.duplicate_count} {noun}")
        invalid_count = len(analysis.invalid_entries)
        if invalid_count:
            noun = "invalid entry" if invalid_count == 1 else "invalid entries"
            removed.append(f"{invalid_count} {noun}")
        if analysis.comment_count:
            noun = "comment line" if analysis.comment_count == 1 else "comment lines"
            removed.append(f"{analysis.comment_count} {noun}")

        kept_noun = "link" if len(analysis.urls) == 1 else "links"
        message = (
            f"Queue cleaned. Kept {len(analysis.urls)} unique {kept_noun}. "
            f"Removed {', '.join(removed)}."
        )
        self._set_status(message, "ready")

    def _clear_urls(self) -> None:
        self.url_input.clear()
        self._set_status("Queue cleared. Paste one or more links to begin.", "ready")

    def _update_queue_summary(self) -> None:
        text = self.url_input.toPlainText()
        analysis = self._get_queue_analysis(text)
        links = len(analysis.urls)
        noun = "link" if links == 1 else "links"
        summary_parts = [f"{count(links)} {noun}"]
        tooltip_parts = [f"{count(links)} unique download {noun} ready."]

        if analysis.duplicate_count:
            duplicate_noun = (
                "duplicate" if analysis.duplicate_count == 1 else "duplicates"
            )
            summary_parts.append(f"{count(analysis.duplicate_count)} {duplicate_noun}")
            tooltip_parts.append("Duplicate links are skipped when downloading.")

        if analysis.invalid_entries:
            invalid_count = len(analysis.invalid_entries)
            summary_parts.append(f"{count(invalid_count)} invalid")
            preview = ", ".join(
                f"{entry.line_number} ({entry.reason})"
                for entry in analysis.invalid_entries[:3]
            )
            if invalid_count > 3:
                preview += ", …"
            tooltip_parts.append(
                f"Invalid lines: {preview}. Use Clean Queue to remove them."
            )

        if analysis.comment_count:
            ignored_noun = "line" if analysis.comment_count == 1 else "lines"
            summary_parts.append(f"{count(analysis.comment_count)} ignored")
            tooltip_parts.append(
                f"{analysis.comment_count} comment {ignored_noun} will be ignored."
            )

        if analysis.invalid_entries and active_skin().state_marks:
            summary_parts.insert(0, "[!]")
        self.queue_label.setText(" · ".join(summary_parts).replace("[!] · ", "[!] "))
        self.queue_label.setToolTip("\n".join(tooltip_parts))
        if analysis.invalid_entries:
            state = "warning"
        elif analysis.duplicate_count or analysis.comment_count:
            state = "notice"
        else:
            state = "ready"
        self._set_widget_state(self.queue_label, state)
        self.clean_urls_button.setEnabled(
            analysis.has_cleanup_items and self.url_input.isEnabled()
        )
        self._queue_count = links
        self._refresh_start_label()
        if self._controls_enabled:
            self._set_activity_priority(False)
        if self._controls_enabled and self._progress_floor:
            # A changed list is a new plan; the last batch's bar no longer applies.
            self._progress_animation.stop()
            self._progress_floor = 0
            self.progress_bar.setValue(0)
        self.empty_state.setVisible(not text.strip())
        self._sync_drop_zone_state()
        self._refresh_plan_summary()

    def _tool_origin(self, path: str) -> str:
        if not path or path == "Not found":
            return "missing"
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
            normalized = os.path.abspath(path)
            if os.path.commonpath([root, normalized]) == root:
                return "bundled"
        except (OSError, ValueError):
            return "system"
        return "system"

    def _refresh_dependency_status(self) -> None:
        ffmpeg_state = "ready" if self._ffmpeg_available else "missing"
        aria_state = "ready" if self._aria2c_available else "missing"
        ffmpeg_origin = self._tool_origin(self._ffmpeg_path)
        aria_origin = self._tool_origin(self._aria2c_path)
        toolchain_text = (
            f"Toolchain: FFmpeg {ffmpeg_state} ({ffmpeg_origin}) | "
            f"aria2c {aria_state} ({aria_origin}) | yt-dlp {self._yt_dlp_version}"
        )
        self.dependency_label.setText(
            f"FFmpeg  ·  {ffmpeg_state} ({ffmpeg_origin})  ·  {_short_version(self._ffmpeg_version)}\n"
            f"aria2c  ·  {aria_state} ({aria_origin})  ·  {_short_version(self._aria2c_version)}\n"
            f"yt-dlp  ·  {self._yt_dlp_version}"
        )
        if toolchain_text != self._last_toolchain_console_text:
            self.append_log(toolchain_text)
            self._last_toolchain_console_text = toolchain_text
        details = [
            f"FFmpeg: {self._ffmpeg_path}",
            f"FFmpeg version: {self._ffmpeg_version}",
            f"aria2c: {self._aria2c_path}",
            f"aria2c version: {self._aria2c_version}",
            f"yt-dlp: {self._yt_dlp_version}",
        ]
        self.dependency_label.setToolTip("\n".join(details))
        if self._ffmpeg_available and self._aria2c_available:
            state = "ready"
        elif self._ffmpeg_available:
            state = "partial"
        else:
            state = "warning"
        self._set_widget_state(self.dependency_label, state)

    def _start_dependency_version_probes(self) -> None:
        """Probe informational tool versions without blocking first paint."""
        probes = (
            ("ffmpeg", self._ffmpeg_path, ["-version"], "_ffmpeg_version"),
            ("aria2c", self._aria2c_path, ["--version"], "_aria2c_version"),
        )
        for name, path, arguments, version_attr in probes:
            if path == "Not found":
                continue
            process = QProcess(self)
            process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            self._dependency_processes[name] = (process, version_attr)
            process.finished.connect(
                lambda _code, _status, key=name, proc=process: (
                    self._finish_dependency_version_probe(key, proc)
                )
            )
            process.errorOccurred.connect(
                lambda _error, key=name, proc=process: (
                    self._finish_dependency_version_probe(key, proc)
                )
            )
            process.start(path, arguments)

    def _finish_dependency_version_probe(
        self,
        name: str,
        process: QProcess,
    ) -> None:
        current = self._dependency_processes.get(name)
        if current is None or current[0] is not process:
            return
        _, version_attr = self._dependency_processes.pop(name)
        output = bytes(process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        version = next(
            (line.strip() for line in output.splitlines() if line.strip()),
            "unknown",
        )
        setattr(self, version_attr, version)
        process.deleteLater()
        self.append_log(f"{name}: {version}")
        self._refresh_dependency_status()

    def _stop_dependency_version_probes(self) -> None:
        processes = list(self._dependency_processes.values())
        self._dependency_processes.clear()
        for process, _version_attr in processes:
            if process.state() != QProcess.ProcessState.NotRunning:
                process.kill()
                process.waitForFinished(1000)
            process.deleteLater()

    def _on_browser_changed(self, browser: str) -> None:
        """Sync field availability and save settings when the source changes."""
        self._update_browser_fields(browser)
        self._save_settings()

    def _cookie_source(self) -> str:
        """Saved value of the cookie source ('None', the file source, or a browser id)."""
        return self.browser_combo.currentData() or "None"

    def _select_cookie_source(self, value: str) -> None:
        index = self.browser_combo.findData(value)
        if index >= 0:
            self.browser_combo.setCurrentIndex(index)

    def _update_browser_fields(self, browser: str) -> None:
        """Profile/keyring/container only apply to a real browser source."""
        browser_active = browser not in ("None", self.COOKIE_FILE_SOURCE)
        for field in (self.profile_input, self.keyring_input, self.container_input):
            field.setEnabled(browser_active)

    def _choose_cookie_file(self) -> None:
        """Open file dialog to select a cookie file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cookie File", "", "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.cookie_file_input.setText(os.path.normpath(path))
            if self._cookie_source() == "None":
                self._select_cookie_source(self.COOKIE_FILE_SOURCE)

    SUPPORTED_BROWSERS = {
        "brave",
        "chrome",
        "chromium",
        "edge",
        "firefox",
        "opera",
        "safari",
        "vivaldi",
    }

    COOKIE_FILE_SOURCE = "Cookie File (Fallback)"

    def _get_cookies_from_browser_tuple(self):
        """Build the cookies_from_browser tuple for yt-dlp."""
        browser = self._cookie_source()
        if browser in ("None", self.COOKIE_FILE_SOURCE):
            return None

        if browser.lower() not in self.SUPPORTED_BROWSERS:
            self.append_log(
                f"Warning: Browser '{browser}' is not supported by yt-dlp. Use Cookie File instead."
            )
            return None

        profile = self.profile_input.text().strip() or None
        keyring = self.keyring_input.text().strip() or None
        container = self.container_input.text().strip() or None

        return (browser, profile, keyring, container)

    def _collect_cookie_settings(self):
        """Return (cookies_from_browser, cookie_file_path, log_lines).

        Exactly one cookie source is active:
        - Browser selected: browser cookies only; a cookie file is ignored.
        - Cookie File (Fallback) selected: the cookies.txt file exclusively.
        - None: no cookies at all.
        """
        browser = self._cookie_source()
        cookie_file = self.cookie_file_input.text().strip() or None
        logs = []

        if browser == "None":
            if cookie_file:
                logs.append(
                    "Cookies: none (a cookie file is set but the source is 'None'; "
                    f"select '{self.COOKIE_FILE_SOURCE}' to use it)"
                )
            else:
                logs.append("Cookies: none")
            return None, None, logs

        if browser == self.COOKIE_FILE_SOURCE:
            if not cookie_file:
                logs.append(
                    f"Warning: '{self.COOKIE_FILE_SOURCE}' is selected but no cookie "
                    "file is set. No cookies will be sent."
                )
                return None, None, logs
            if not os.path.isfile(cookie_file):
                logs.append(f"Warning: Cookie file not found: {cookie_file}")
            logs.append(f"Cookies: file {cookie_file} (exclusive)")
            return None, cookie_file, logs

        if cookie_file:
            logs.append(
                f"Cookies: browser '{browser}' (cookie file '{cookie_file}' ignored; "
                f"select '{self.COOKIE_FILE_SOURCE}' to use the file instead)"
            )
        else:
            logs.append(f"Cookies: browser '{browser}'")
        return self._get_cookies_from_browser_tuple(), None, logs

    def _show_cookie_help(self) -> None:
        """Show a help dialog explaining how to use cookie fetching."""
        dialog = QDialog(self)
        dialog.setObjectName("HelpDialog")
        dialog.setWindowTitle("Cookie guide")
        dialog.setMinimumSize(560, 480)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Cookie guide", dialog)
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        help_text = QTextBrowser(dialog)
        help_text.setOpenExternalLinks(True)
        html = """
        <style>
            body { color: #e8e6f0; font-family: Roboto, 'Segoe UI', Arial, sans-serif; font-size: 10pt; }
            h3 { color: #bd9bff; margin-top: 16px; margin-bottom: 8px; }
            p { margin: 6px 0; line-height: 1.5; }
            ul { margin-left: 20px; }
            li { margin: 4px 0; }
            code { background-color: #302f3a; padding: 2px 6px; color: #7fd4a3; }
            .warning { color: #f0c063; }
            .browser { color: #bd9bff; }
        </style>
        
        <h3>Why Use Cookies?</h3>
        <p>Cookies allow you to download:</p>
        <ul>
            <li>Age-restricted content</li>
            <li>Members-only/Premium videos</li>
            <li>Private videos you have access to</li>
            <li>Higher quality streams (some sites)</li>
        </ul>
        
        <h3>Supported Browsers</h3>
        <p>Select your browser from the dropdown:</p>
        <ul>
            <li><span class="browser">Chrome</span> - Google Chrome</li>
            <li><span class="browser">Firefox</span> - Mozilla Firefox</li>
            <li><span class="browser">Edge</span> - Microsoft Edge</li>
            <li><span class="browser">Brave</span> - Brave Browser</li>
            <li><span class="browser">Opera</span> - Opera / Opera GX</li>
            <li><span class="browser">Vivaldi</span> - Vivaldi Browser</li>
            <li><span class="browser">Chromium</span> - Chromium-based browsers</li>
            <li><span class="browser">Safari</span> - Safari (macOS only)</li>
        </ul>
        
        <h3>Other Browsers (Thorium, etc.)</h3>
        <p>For Chromium forks like <b>Thorium</b>, <b>Ungoogled Chromium</b>, or others not listed:</p>
        <ul>
            <li>These browsers are not directly supported by yt-dlp's browser cookie fetching.</li>
            <li>Please use the <b>Cookie File (Fallback)</b> method below.</li>
        </ul>
        
        <h3>Browser Profiles</h3>
        <p>If you have multiple browser profiles:</p>
        <ul>
            <li>Enter the profile name (e.g., <code>Default</code>, <code>Profile 1</code>)</li>
            <li>Leave empty to use the default profile</li>
        </ul>
        
        <h3>Firefox Containers</h3>
        <p>If using Firefox Multi-Account Containers:</p>
        <ul>
            <li>Enter the container name (e.g., <code>Personal</code>, <code>Work</code>)</li>
        </ul>
        
        <h3 class="warning">⚠️ Important Tips</h3>
        <ul>
            <li><b>Close your browser</b> before downloading to avoid cookie database locks</li>
            <li>Make sure you're <b>logged in</b> to the site in your browser first</li>
            <li>Some browsers encrypt cookies - this may require additional setup on Linux</li>
        </ul>
        
        <h3>Cookie File (Fallback)</h3>
        <p>If browser cookies don't work, export cookies manually and use them exclusively:</p>
        <ul>
            <li>Use a browser extension like "Get cookies.txt LOCALLY"</li>
            <li>Export to Netscape format (.txt file)</li>
            <li>Select the file in the "Cookie File (Fallback)" section</li>
            <li>Set the Browser dropdown to <b>Cookie File (Fallback)</b></li>
        </ul>
        <p>When selected, the cookie file is the <b>only</b> cookie source. The browser dropdown is ignored.</p>
        
        <p style="margin-top: 20px; color: #aaa7b7;">
            For more info, see:
            <a href="https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp" style="color: #bd9bff;">yt-dlp Cookie FAQ</a>
        </p>
        """
        # The guide was written in Default's inks; map them to the active skin.
        for old, role in (
            ("#e8e6f0", "text"), ("#bd9bff", "focus"), ("#302f3a", "raised"),
            ("#7fd4a3", "success"), ("#f0c063", "warning"), ("#aaa7b7", "muted"),
        ):
            html = html.replace(old, COLORS[role])
        families = ", ".join(f"'{name}'" for name in active_skin().fonts)
        help_text.setHtml(html.replace("Roboto, 'Segoe UI'", families))
        layout.addWidget(help_text, 1)

        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setFixedWidth(100)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        strip_native_frames(dialog)
        dialog.exec()

    def _show_history_dialog(self) -> None:
        dialog = HistoryDialog(self._history, self)
        if dialog.exec() == QDialog.Accepted:
            retry_urls = dialog.get_retry_urls()
            if retry_urls:
                self._add_urls_to_queue(retry_urls, "download history")

    def _set_live_console_status(self, message: str) -> None:
        """Replace the trailing live-status line instead of flooding the console."""
        if not self._live_status_active:
            self.log_output.appendPlainText(message)
            self._live_status_active = True
        else:
            cursor = QTextCursor(self.log_output.document())
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(
                QTextCursor.MoveOperation.StartOfBlock,
                QTextCursor.MoveMode.KeepAnchor,
            )
            cursor.insertText(message)
        self.log_output.ensureCursorVisible()

    def append_log(self, message: str) -> None:
        self._live_status_active = False
        self.log_output.appendPlainText(message)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.dir_input.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.open_folder_button.setEnabled(True)
        self.url_input.setEnabled(enabled)
        self.mp3_btn.setEnabled(enabled)
        self.mp4_btn.setEnabled(enabled)
        self.quality_combo.setEnabled(enabled)
        self.template_presets.setEnabled(enabled)
        self.template_line.setEnabled(enabled)
        self.ffmpeg_input.setEnabled(enabled)
        self.ffmpeg_mode.setEnabled(enabled)
        self.playlist_checkbox.setEnabled(enabled)
        self.restrict_checkbox.setEnabled(enabled)
        self.async_checkbox.setEnabled(enabled)
        self.aria2c_checkbox.setEnabled(enabled)
        self.import_urls_button.setEnabled(enabled)
        self.clean_urls_button.setEnabled(
            enabled and self._get_queue_analysis().has_cleanup_items
        )
        self.clear_urls_button.setEnabled(enabled)
        self.history_button.setEnabled(True)
        self._controls_enabled = enabled
        self.check_network_button.setEnabled(
            enabled and self._network_socket is None
        )
        self.paste_button.setEnabled(enabled)
        # Idle shows one clear action; a running batch shows its transport.
        self.start_button.setEnabled(enabled)
        self.start_button.setVisible(enabled)
        for button in (self.cancel_button, self.pause_button, self.skip_button):
            button.setEnabled(not enabled)
            button.setVisible(not enabled)
        if enabled:
            self._paused = False
            self._set_pause_button(paused=False)
            self._refresh_plan_summary()
        else:
            self._set_activity_priority(True)
            # Disabling the editor would push focus onto the next button.
            self.session_list.setFocus(Qt.FocusReason.OtherFocusReason)

    def _set_pause_button(self, *, paused: bool) -> None:
        if active_skin().icon_actions:
            self.pause_button.setIcon(line_icon("resume" if paused else "pause"))
            self.pause_button.setText("")
        else:
            self.pause_button.setIcon(QIcon())
            self.pause_button.setText("[resume]" if paused else "[pause]")
        self.pause_button.setAccessibleName("Resume download" if paused else "Pause download")
        self.pause_button.setToolTip("Resume downloads" if paused else "Pause downloads")

    def _check_network_status(self) -> None:
        """Start a cancellable, non-blocking TCP connectivity check."""
        self._cancel_network_check()
        self._network_state = "pending"
        self._render_network()
        self.network_label.setToolTip("Checking the internet connection")
        self.append_log("Network status: Checking...")
        self.check_network_button.setEnabled(False)

        socket = QTcpSocket(self)
        self._network_socket = socket
        socket.connected.connect(
            lambda current=socket: self._finish_network_check(current, True)
        )
        socket.errorOccurred.connect(
            lambda _error, current=socket: self._finish_network_check(
                current, False
            )
        )
        self._network_timer.start(5000)
        socket.connectToHost("8.8.8.8", 53)

    def _on_network_timeout(self) -> None:
        socket = self._network_socket
        if socket is not None:
            self._finish_network_check(socket, False)

    def _finish_network_check(self, socket: QTcpSocket, is_online: bool) -> None:
        if socket is not self._network_socket:
            return
        self._network_socket = None
        self._network_timer.stop()
        socket.abort()
        socket.deleteLater()

        ytdlp_ver = self._yt_dlp_version or "unknown"
        self._network_state = "online" if is_online else "offline"
        self._render_network()
        if is_online:
            self.network_label.setToolTip(f"Internet reachable · yt-dlp {ytdlp_ver}")
            self.append_log(f"Network status: Online | yt-dlp: {ytdlp_ver}")
        else:
            self.network_label.setToolTip(
                f"Internet not reachable, downloads may fail · yt-dlp {ytdlp_ver}"
            )
            self.append_log(
                f"Network status: Offline | yt-dlp: {ytdlp_ver} - downloads may fail"
            )
        self.check_network_button.setEnabled(self._controls_enabled)

    def _cancel_network_check(self) -> None:
        self._network_timer.stop()
        socket = self._network_socket
        self._network_socket = None
        if socket is not None:
            socket.abort()
            socket.deleteLater()

    def _toggle_pause(self) -> None:
        worker = self._worker or self._async_worker
        if not worker:
            return

        if worker.is_paused():
            worker.resume()
            self._paused = False
            self.append_log("Download resumed")
        else:
            worker.pause()
            self._paused = True
            self.append_log("Download paused")
        self._set_pause_button(paused=self._paused)
        self._refresh_download_headline()

    def _collect_urls(self) -> List[str]:
        return list(self._get_queue_analysis().urls)

    def _validate_inputs(self) -> Optional[str]:
        analysis = self._get_queue_analysis()
        if analysis.invalid_entries:
            first = analysis.invalid_entries[0]
            remaining = len(analysis.invalid_entries) - 1
            detail = f"Line {first.line_number} {first.reason}."
            if remaining:
                noun = "entry" if remaining == 1 else "entries"
                detail += f" {remaining} more invalid {noun}."
            return (
                f"{detail}\n"
                "Replace invalid entries with full HTTP(S) links, or use Clean Queue to remove them."
            )
        if not analysis.urls:
            return "Add at least one link, one per line."
        directory = self.dir_input.text().strip()
        if not directory:
            return "Please choose a download directory."
        if self.aria2c_checkbox.isChecked() and not self._aria2c_available:
            return (
                "aria2c is enabled but aria2c.exe was not found.\n"
                "Place aria2c.exe beside YTDLE.exe, keep it in the project folder when running from source, "
                "or turn off Multi-connection downloads on the Options page."
            )
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            return f"Cannot create directory:\n{directory}\n{e}"
        return None

    def _start_downloads(self) -> None:
        if not self._controls_enabled:
            return
        error = self._validate_inputs()
        if error:
            # Explain the problem in place and put the cursor where the fix goes.
            self._show_page(0)
            self._set_status(error, "error")
            if error.startswith(("Please choose", "Cannot create")):
                self.dir_input.setFocus(Qt.FocusReason.OtherFocusReason)
            elif not error.startswith("aria2c"):
                self.url_input.setFocus(Qt.FocusReason.OtherFocusReason)
            return

        queue_analysis = self._get_queue_analysis()
        urls = list(queue_analysis.urls)
        self._downloading_total = len(urls)
        self._downloading_started = 0
        self._downloading_completed = 0
        self._downloading_active = 0

        # Determine ffmpeg args based on mode
        f_args = self.ffmpeg_input.text().strip()
        f_mode = self.ffmpeg_mode.currentText()

        f_add = f_args if f_mode == "Append" else None
        f_override = f_args if f_mode == "Override" else None

        # Determine if using async mode
        use_async = self.async_checkbox.isChecked()
        use_aria2c = self.aria2c_checkbox.isChecked()

        cookies_from_browser, cookie_file, cookie_logs = self._collect_cookie_settings()

        opts = DownloadOptions(
            is_mp3=self.mp3_btn.isChecked(),
            quality=self.quality_combo.currentText(),
            outtmpl_template=self.template_line.text(),
            directory=self.dir_input.text().strip(),
            download_playlist=self.playlist_checkbox.isChecked(),
            restrict_filenames=self.restrict_checkbox.isChecked(),
            ffmpeg_add_args=f_add if f_add else None,
            ffmpeg_override_args=f_override if f_override else None,
            cookies_from_browser=cookies_from_browser,
            cookies=cookie_file,
            use_aria2c=use_aria2c,
            max_connections=16,
            max_concurrent_downloads=3,
        )

        self._set_controls_enabled(False)
        self._progress_animation.stop()
        self.progress_bar.setValue(0)
        self._progress_floor = 0
        self.session_list.start_session(urls)
        self.activity_items_button.setChecked(True)
        self.activity_stack.setCurrentIndex(0)
        self._set_status("Starting download...", "active")
        self.status_detail.setText(
            f"{'MP3' if opts.is_mp3 else 'MP4'} {opts.quality} · to {opts.directory}"
        )
        self.append_log(
            f"System: yt-dlp {self._yt_dlp_version}, ffmpeg: {self._ffmpeg_path}"
        )
        self.append_log(f"aria2c: {self._aria2c_path}")
        self.append_log(f"Queue size: {len(urls)}")
        if queue_analysis.duplicate_count:
            noun = "duplicate" if queue_analysis.duplicate_count == 1 else "duplicates"
            self.append_log(f"Queue: skipped {queue_analysis.duplicate_count} {noun}.")
        self.append_log(
            f"Format: {'MP3' if opts.is_mp3 else 'MP4'} | Quality: {opts.quality}"
        )
        self.append_log(f"Output dir: {opts.directory}")
        self.append_log(f"Template: {opts.outtmpl_template}.%(ext)s")
        self.append_log(
            f"Playlist: {'Yes' if opts.download_playlist else 'No'} | Restrict filenames: {'Yes' if opts.restrict_filenames else 'No'}"
        )
        for cookie_log in cookie_logs:
            self.append_log(cookie_log)
        self.append_log(
            f"Async mode: {'Yes' if use_async else 'No'} | Aria2c: {'Yes' if use_aria2c else 'No'}"
        )
        if not self._ffmpeg_available:
            self.append_log(
                "Warning: ffmpeg not found on PATH. Audio extraction and metadata embedding may fail."
            )

        if use_async:
            # Defer the heavy yt-dlp engine import until a download is requested.
            from core.async_manager import AsyncVideoDownloadWorker

            self._worker_thread = QThread(self)
            self._async_worker = AsyncVideoDownloadWorker(
                urls, opts, history=self._history, max_concurrent=3
            )
            self._async_worker.moveToThread(self._worker_thread)

            self._worker_thread.started.connect(self._async_worker.run)
            self._async_worker.progress.connect(self._on_progress)
            self._async_worker.status.connect(self._on_status)
            self._async_worker.itemStarted.connect(self._on_item_started)
            self._async_worker.itemFinished.connect(self._on_item_finished)
            self._async_worker.allFinished.connect(self._on_all_finished)
            self._async_worker.error.connect(self._on_error)
            self._async_worker.log.connect(self.append_log)

            self._worker_thread.finished.connect(self._cleanup_worker)
            self._worker_thread.start()
        else:
            # Keep the legacy engine available without charging GUI startup for it.
            from core.downloader import VideoDownloadWorker

            self._worker_thread = QThread(self)
            self._worker = VideoDownloadWorker(urls, opts, history=self._history)
            self._worker.moveToThread(self._worker_thread)

            self._worker_thread.started.connect(self._worker.run)
            self._worker.progress.connect(self._on_progress)
            self._worker.status.connect(self._on_status)
            self._worker.itemStarted.connect(self._on_item_started)
            self._worker.itemFinished.connect(self._on_item_finished)
            self._worker.allFinished.connect(self._on_all_finished)
            self._worker.error.connect(self._on_error)
            self._worker.log.connect(self.append_log)

            self._worker_thread.finished.connect(self._cleanup_worker)
            self._worker_thread.start()

    def _cancel_downloads(self) -> None:
        worker = self._worker or self._async_worker
        if worker:
            self._set_status("Cancelling...", "active")
            self.cancel_button.setEnabled(False)
            worker.cancel()

    def _skip_current(self) -> None:
        worker = self._worker or self._async_worker
        if worker:
            self._set_status("Skipping...", "active")
            self.skip_button.setEnabled(False)
            worker.skip_current()

    def _on_progress(self, value: int) -> None:
        """Map per-item percentages onto one batch bar that never moves backward."""
        value = max(0, min(100, value))
        total = max(1, self._downloading_total)
        overall = (self._downloading_completed * 100 + value) // total
        self._advance_progress(overall)

    def _advance_progress(self, overall: int, *, final: bool = False) -> None:
        overall = max(self._progress_floor, min(100 if final else 99, overall))
        animating = (
            self._progress_animation.state() == QPropertyAnimation.State.Running
        )
        if overall == self._progress_floor and (
            animating or self.progress_bar.value() == overall
        ):
            return
        self._progress_floor = overall
        self._progress_animation.stop()
        self._progress_animation.setStartValue(self.progress_bar.value())
        self._progress_animation.setEndValue(overall)
        self._progress_animation.start()
        self.setWindowTitle(f"{overall}% · {_APP_TITLE}")

    def _refresh_download_headline(self) -> None:
        if self._controls_enabled:
            return
        done, total = self._downloading_completed, self._downloading_total
        if self._paused:
            headline, state = "Paused", "warning"
        elif total > 1:
            headline, state = f"Downloading · {count(done)} of {count(total)} finished", "active"
        else:
            headline, state = "Downloading", "active"
        self._render_headline(headline, state)

    def _on_status(self, text: str) -> None:
        prefix = ""
        if self._downloading_total:
            prefix = (
                f"Completed {self._downloading_completed}/{self._downloading_total}"
                f" | Active {self._downloading_active}: "
            )
        self.status_detail.setText(text)
        self._set_live_console_status(f"Status: {prefix}{text}")

    def _on_item_started(self, url: str) -> None:
        self._downloading_started += 1
        self._downloading_active += 1
        self.session_list.set_state(url, "active")
        self._refresh_download_headline()
        self.append_log(
            f"Starting {self._downloading_started}/{self._downloading_total}: {url}"
        )

    def _on_item_finished(self, url: str, success: bool, info: str) -> None:
        self._downloading_active = max(0, self._downloading_active - 1)
        self._downloading_completed += 1
        if success:
            path = "" if info == "Completed" else info
            self.session_list.set_state(url, "done", path)
            self.append_log(f"SUCCESS: {url}\nSaved to: {info}")
        else:
            if info == "Skipped":
                self.session_list.set_state(url, "skipped")
            elif info == "Cancelled":
                self.session_list.set_state(url, "stopped")
            else:
                reason = info.strip().removeprefix("ERROR:").strip().splitlines()
                self.session_list.set_state(url, "failed", reason[0] if reason else "")
            self.append_log(f"FAILED: {url}\nReason: {info}")
        total = max(1, self._downloading_total)
        self._advance_progress(self._downloading_completed * 100 // total)
        self._refresh_download_headline()

    def _on_all_finished(self, success_count: int, fail_count: int) -> None:
        self.append_log(f"All done. Success: {success_count}, Failed: {fail_count}")
        self.session_list.finish_session()
        counts = self.session_list.counts()
        not_saved = counts["skipped"] + counts["stopped"]
        saved_noun = "download" if success_count == 1 else "downloads"
        if fail_count > 0:
            self._set_status(
                f"{count(success_count)} saved, {count(fail_count)} failed",
                "warning" if success_count else "error",
            )
            hint = "Failed links stay in History, ready to retry."
        elif success_count == 0:
            self._set_status("Stopped. Nothing was saved.", "warning")
            hint = "Press Download to start again."
        else:
            headline = f"All {count(success_count)} {saved_noun} saved"
            if not_saved:
                headline = f"{count(success_count)} saved, {count(not_saved)} not downloaded"
            elif success_count == 1:
                headline = "Saved"
            self._set_status(headline, "done")
            hint = "Double-click a saved row to show the file."

        self._set_controls_enabled(True)
        if not counts["stopped"]:
            self._advance_progress(100, final=True)
        self.status_detail.setText(hint)
        self.setWindowTitle(_APP_TITLE)
        if not self.isActiveWindow():
            QApplication.alert(self)

        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()

    def _reveal_session_item(self, item) -> None:
        """Show a saved file selected in Explorer, or open its folder elsewhere."""
        path = self.session_list.item_detail(item)
        if self.session_list.item_state(item) != "done" or not path:
            return
        if not os.path.exists(path):
            open_in_file_manager(os.path.dirname(path) or self.dir_input.text().strip())
            return
        if sys.platform == "win32":
            process = QProcess(self)
            process.setProgram("explorer.exe")
            process.setNativeArguments(f'/select,"{os.path.normpath(path)}"')
            if process.startDetached():
                return
        open_in_file_manager(os.path.dirname(path))

    def _on_error(self, message: str) -> None:
        self._set_status(message, "error")

    def _cleanup_worker(self) -> None:
        if self._worker:
            try:
                self._worker.deleteLater()
            except RuntimeError as error:
                logger.debug(
                    "Synchronous worker was already deleted: %s", error, exc_info=True
                )
            self._worker = None
        if self._async_worker:
            try:
                self._async_worker.deleteLater()
            except RuntimeError as error:
                logger.debug(
                    "Asynchronous worker was already deleted: %s", error, exc_info=True
                )
            self._async_worker = None
        if self._worker_thread:
            try:
                self._worker_thread.deleteLater()
            except RuntimeError as error:
                logger.debug(
                    "Worker thread was already deleted: %s", error, exc_info=True
                )
            self._worker_thread = None

    def _warn_ffmpeg(self) -> None:
        self._set_status(
            "ffmpeg not found. Some formats may not process. Consider installing ffmpeg.",
            "warning",
        )
        self.append_log(
            "ffmpeg not found on PATH. Audio extraction (MP3) and metadata embedding require ffmpeg."
        )

    def closeEvent(self, event) -> None:
        if self._settings_save_timer.isActive():
            self._settings_save_timer.stop()
            self._save_settings_now()
        self._cancel_network_check()
        self._stop_dependency_version_probes()
        worker = self._worker or self._async_worker
        if worker:
            try:
                worker.cancel()
            except RuntimeError as error:
                logger.warning(
                    "Could not cancel the active worker during shutdown: %s",
                    error,
                    exc_info=True,
                )
        if self._worker_thread and self._worker_thread.isRunning():
            try:
                self._worker_thread.quit()
                self._worker_thread.wait(5000)
            except RuntimeError as error:
                logger.warning(
                    "Could not stop the worker thread during shutdown: %s",
                    error,
                    exc_info=True,
                )
        if not self._worker_thread or not self._worker_thread.isRunning():
            close_history = getattr(self._history, "close", None)
            if close_history is not None:
                close_history()
        super().closeEvent(event)
