from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Iterable, List, Optional

from PySide6.QtCore import QProcess, QSettings, QThread, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtNetwork import QTcpSocket
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
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
    QTabWidget,
    QGroupBox,
    QDialog,
    QTextBrowser,
)

from core.config import DownloadOptions
from core.dependencies import resolve_dependency_paths
from core.history import DownloadHistory
from core.utils import open_in_file_manager
from ui.components import HistoryDialog
from ui.components.title_bar import CustomTitleBar
from ui.components.toggle_switch import ToggleSwitch
from ui.icons import line_icon
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

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
        self._load_settings()
        self.setAcceptDrops(True)
        self._start_dependency_version_probes()

        if not self._ffmpeg_available:
            self._warn_ffmpeg()

    def _init_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 6, 10, 8)
        root.setSpacing(5)

        self.title_bar = CustomTitleBar(self)
        root.addWidget(self.title_bar)

        # Tab widget for Download and Cookies
        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs, 1)

        download_tab = QWidget()
        download_layout = QVBoxLayout(download_tab)
        download_layout.setContentsMargins(8, 8, 8, 8)
        download_layout.setSpacing(5)

        dir_row = QHBoxLayout()
        dir_label = QLabel("Directory:", self)
        dir_label.setToolTip("Folder where files will be saved.")
        self.dir_input = QLineEdit(self)
        self.dir_input.setPlaceholderText("Download directory")
        self.dir_input.setToolTip("Folder where files will be saved.")
        dir_row.setSpacing(6)
        dir_row.addWidget(dir_label, 0)
        dir_row.addWidget(self.dir_input, 1)

        self.browse_button = QToolButton(self)
        self.browse_button.setObjectName("BrowseButton")
        self.browse_button.setIcon(line_icon("folder"))
        self.browse_button.setToolTip("Choose download directory")
        self.browse_button.setAccessibleName("Choose download directory")
        self.browse_button.clicked.connect(self._choose_directory)
        dir_row.addWidget(self.browse_button, 0)

        self.open_folder_button = QToolButton(self)
        self.open_folder_button.setObjectName("OpenFolderButton")
        self.open_folder_button.setIcon(line_icon("open-folder"))
        self.open_folder_button.setToolTip(
            "Open the current download folder in your file manager"
        )
        self.open_folder_button.setAccessibleName("Open current download folder")
        self.open_folder_button.clicked.connect(self._open_folder)
        dir_row.addWidget(self.open_folder_button, 0)

        download_layout.addLayout(dir_row)

        dependency_row = QHBoxLayout()
        self.dependency_label = QLabel("Checking tools...", self)
        self.dependency_label.setObjectName("DependencyStatus")
        self.dependency_label.setProperty("state", "pending")
        self.dependency_label.setAccessibleName("Toolchain status")
        self.dependency_label.setVisible(False)
        self.dependency_label.setWordWrap(True)
        self.dependency_label.setToolTip(
            "Detected downloader toolchain and local paths"
        )
        dependency_row.addWidget(self.dependency_label, 1)
        download_layout.addLayout(dependency_row)

        url_header = QHBoxLayout()
        url_label = QLabel("URLs:", self)
        url_label.setToolTip(
            "Paste one URL per line. You can also drag & drop links here."
        )
        url_header.addWidget(url_label, 0)
        self.queue_label = QLabel("Queue: 0 links", self)
        self.queue_label.setObjectName("QueueSummary")
        self.queue_label.setToolTip("How many non-empty lines are queued")
        url_header.addWidget(self.queue_label, 0)
        url_header.addStretch(1)

        self.import_urls_button = QPushButton("Import List", self)
        self.import_urls_button.setObjectName("ImportUrlsButton")
        self.import_urls_button.setToolTip("Add links from a UTF-8 text file")
        self.import_urls_button.clicked.connect(self._import_url_list)
        url_header.addWidget(self.import_urls_button, 0)

        self.clean_urls_button = QPushButton("Clean Queue", self)
        self.clean_urls_button.setObjectName("CleanUrlsButton")
        self.clean_urls_button.setToolTip(
            "Remove duplicate, invalid, and comment lines"
        )
        self.clean_urls_button.clicked.connect(self._clean_url_queue)
        self.clean_urls_button.setEnabled(False)
        url_header.addWidget(self.clean_urls_button, 0)

        self.clear_urls_button = QPushButton("Clear URLs", self)
        self.clear_urls_button.setObjectName("ClearUrlsButton")
        self.clear_urls_button.setToolTip("Clear the current URL queue")
        self.clear_urls_button.clicked.connect(self._clear_urls)
        url_header.addWidget(self.clear_urls_button, 0)
        download_layout.addLayout(url_header)

        self.url_input = QPlainTextEdit(self)
        self.url_input.setPlaceholderText(
            "Enter one URL per line (YouTube, Twitter, TikTok, etc.)"
        )
        self.url_input.setTabChangesFocus(True)
        self.url_input.setAccessibleName("Download URLs")
        self.url_input.setMinimumHeight(88)
        self.url_input.setToolTip(
            "Paste one URL per line. You can also drag & drop links here."
        )
        download_layout.addWidget(self.url_input, 1)

        fmt_row = QHBoxLayout()

        fmt_label = QLabel("Format:", self)
        fmt_label.setToolTip("Choose MP3 for audio-only, or MP4 for full video.")
        fmt_row.setSpacing(6)
        fmt_row.addWidget(fmt_label, 0)

        self.format_switch = QFrame(self)
        self.format_switch.setObjectName("FormatSwitch")
        format_switch_layout = QHBoxLayout(self.format_switch)
        format_switch_layout.setContentsMargins(0, 0, 0, 0)
        format_switch_layout.setSpacing(0)

        self.mp3_btn = QPushButton("MP3", self.format_switch)
        self.mp3_btn.setObjectName("FormatSegmentLeft")
        self.mp3_btn.setCheckable(True)
        self.mp3_btn.setProperty("formatToggle", True)
        self.mp3_btn.setToolTip(
            "Audio-only download. Converts best audio to MP3 at the selected bitrate."
        )

        self.mp4_btn = QPushButton("MP4", self.format_switch)
        self.mp4_btn.setObjectName("FormatSegmentRight")
        self.mp4_btn.setCheckable(True)
        self.mp4_btn.setProperty("formatToggle", True)
        self.mp4_btn.setToolTip(
            "Video download (MP4). Respects the maximum resolution you select."
        )

        self.fmt_group = QButtonGroup(self)
        self.fmt_group.setExclusive(True)
        self.fmt_group.addButton(self.mp3_btn)
        self.fmt_group.addButton(self.mp4_btn)
        format_switch_layout.addWidget(self.mp3_btn)
        format_switch_layout.addWidget(self.mp4_btn)
        fmt_row.addWidget(self.format_switch, 0)

        fmt_row.addSpacing(10)

        qual_label = QLabel("Quality:", self)
        qual_label.setToolTip(
            "MP3: bitrate (kbps). MP4: maximum video resolution. 'Best' picks the highest available."
        )
        fmt_row.addWidget(qual_label, 0)

        self.quality_combo = QComboBox(self)
        self.quality_combo.setToolTip(
            "Select bitrate for MP3, or resolution cap for MP4."
        )
        fmt_row.addWidget(self.quality_combo, 0)

        fmt_row.addStretch(1)
        download_layout.addLayout(fmt_row)

        tmpl_row = QHBoxLayout()
        tmpl_label = QLabel("Output template:", self)
        tmpl_label.setToolTip(
            "Naming pattern (yt_dlp template). The file extension is added automatically."
        )
        tmpl_row.setSpacing(6)
        tmpl_row.addWidget(tmpl_label, 0)

        self.template_presets = QComboBox(self)
        self.template_presets.addItems(
            [
                "%(title).150s",
                "%(uploader)s - %(title).150s",
                "%(playlist_title)s/%(playlist_index)03d - %(title).150s",
                "%(channel)s/%(upload_date)s - %(title).100s",
            ]
        )
        self.template_presets.setToolTip(
            "Pick a common naming pattern for file names/folders."
        )
        tmpl_row.addWidget(self.template_presets, 0)

        self.template_line = QLineEdit(self)
        self.template_line.setPlaceholderText("%(title).150s")
        self.template_line.setToolTip(
            "Freeform yt_dlp output template (no extension). Example: %(uploader)s - %(title).150s"
        )
        tmpl_row.addWidget(self.template_line, 1)
        download_layout.addLayout(tmpl_row)

        ffmpeg_row = QHBoxLayout()
        ffmpeg_label = QLabel("FFmpeg Args:", self)
        ffmpeg_label.setToolTip(
            "Custom FFmpeg arguments (e.g. -vcodec libx264). Optional."
        )
        ffmpeg_row.setSpacing(6)
        ffmpeg_row.addWidget(ffmpeg_label, 0)

        self.ffmpeg_input = QLineEdit(self)
        self.ffmpeg_input.setPlaceholderText(
            "Optional: Custom FFmpeg args (e.g. -vcodec libx264)"
        )
        self.ffmpeg_input.setToolTip("Pass extra arguments to FFmpeg post-processor.")
        ffmpeg_row.addWidget(self.ffmpeg_input, 1)

        self.ffmpeg_mode = QComboBox(self)
        self.ffmpeg_mode.addItems(["Append", "Override"])
        self.ffmpeg_mode.setToolTip(
            "Append: Add to defaults. Override: Replace/Force specific args."
        )
        self.ffmpeg_mode.setFixedWidth(108)
        ffmpeg_row.addWidget(self.ffmpeg_mode, 0)

        download_layout.addLayout(ffmpeg_row)

        opt_row = QHBoxLayout()
        self.playlist_checkbox = ToggleSwitch("Download playlist", self)
        self.playlist_checkbox.setToolTip(
            "If the link is a playlist/series, download all items. Otherwise only the single video."
        )
        self.restrict_checkbox = ToggleSwitch("Restrict filenames", self)
        self.restrict_checkbox.setToolTip(
            "Use only ASCII-safe characters in file names (helps on some filesystems)."
        )
        self.async_checkbox = ToggleSwitch("Async mode", self)
        self.async_checkbox.setToolTip(
            "Use async download manager for better concurrency and performance"
        )
        self.async_checkbox.setChecked(True)
        self.aria2c_checkbox = ToggleSwitch("Use aria2c", self)
        self.aria2c_checkbox.setToolTip(
            "Use aria2c for multi-connection downloads (faster but requires aria2c binary)"
        )
        opt_row.addWidget(self.playlist_checkbox, 0)
        opt_row.addWidget(self.restrict_checkbox, 0)
        opt_row.addWidget(self.async_checkbox, 0)
        opt_row.addWidget(self.aria2c_checkbox, 0)
        opt_row.addStretch(1)
        opt_row.setSpacing(4)
        download_layout.addLayout(opt_row)

        actions_row = QHBoxLayout()
        self.history_button = QPushButton("History", self)
        self.history_button.setObjectName("HistoryButton")
        self.history_button.setToolTip(
            "View download history and manage failed downloads"
        )
        self.history_button.clicked.connect(self._show_history_dialog)

        self.network_label = QLabel("Network: Checking...", self)
        self.network_label.setObjectName("NetworkLabel")
        self.network_label.setProperty("state", "pending")
        self.network_label.setAccessibleName("Network status")
        self.network_label.setVisible(False)
        self.network_label.setToolTip("Current network connection status")

        self.check_network_button = QPushButton("Check Network", self)
        self.check_network_button.setObjectName("CheckNetworkButton")
        self.check_network_button.setToolTip("Manually check internet connection")
        self.check_network_button.clicked.connect(self._check_network_status)

        actions_row.addWidget(self.history_button, 0)
        actions_row.addWidget(self.network_label, 0)
        actions_row.addWidget(self.check_network_button, 0)
        actions_row.addStretch(1)
        actions_row.setSpacing(4)
        download_layout.addLayout(actions_row)

        transport_row = QHBoxLayout()
        transport_row.addStretch(1)

        self.start_button = QPushButton("Start Download", self)
        self.start_button.setObjectName("DownloadButton")
        self.start_button.setToolTip("Start downloading all URLs in the list")
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setToolTip(
            "Request a safe stop after the current file finishes processing"
        )
        self.cancel_button.setEnabled(False)
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setObjectName("PauseButton")
        self.pause_button.setToolTip("Pause the current download")
        self.pause_button.setEnabled(False)
        self.skip_button = QPushButton("Skip", self)
        self.skip_button.setObjectName("SkipButton")
        self.skip_button.setToolTip("Skip the current download and move to the next")
        self.skip_button.setEnabled(False)
        transport_row.addWidget(self.start_button, 0)
        transport_row.addWidget(self.cancel_button, 0)
        transport_row.addWidget(self.pause_button, 0)
        transport_row.addWidget(self.skip_button, 0)
        transport_row.setSpacing(4)
        download_layout.addLayout(transport_row)

        self.tabs.addTab(download_tab, "Download")

        cookies_tab = QWidget()
        cookies_layout = QVBoxLayout(cookies_tab)
        cookies_layout.setContentsMargins(8, 8, 8, 8)
        cookies_layout.setSpacing(8)

        # Browser cookies group
        browser_group = QGroupBox("Browser Cookies", self)
        browser_group_layout = QVBoxLayout(browser_group)
        browser_group_layout.setSpacing(6)

        browser_row = QHBoxLayout()
        browser_label = QLabel("Browser:", self)
        browser_label.setToolTip(
            "Select browser to fetch cookies from. Only officially supported browsers work."
        )
        self.browser_combo = QComboBox(self)
        self.browser_combo.addItems(
            [
                "None",
                "Cookie File (Fallback)",
                "brave",
                "chrome",
                "chromium",
                "edge",
                "firefox",
                "opera",
                "safari",
                "vivaldi",
            ]
        )
        self.browser_combo.setToolTip(
            "Cookie source. Exactly one source is used:\n"
            "- None: send no cookies.\n"
            "- Cookie File (Fallback): use the cookies.txt file below exclusively.\n"
            "- Browser name: read cookies from that browser only.\n"
            "For Chromium forks (Thorium, Ungoogled, etc.), select Cookie File (Fallback)."
        )
        self.browser_combo.currentTextChanged.connect(self._on_browser_changed)
        browser_row.addWidget(browser_label, 0)
        browser_row.addWidget(self.browser_combo, 1)
        browser_group_layout.addLayout(browser_row)

        profile_row = QHBoxLayout()
        profile_label = QLabel("Profile:", self)
        profile_label.setToolTip(
            "Browser profile name (optional). Leave empty for default profile."
        )
        self.profile_input = QLineEdit(self)
        self.profile_input.setPlaceholderText(
            "Optional: Browser profile name (e.g., 'Default', 'Profile 1')"
        )
        self.profile_input.setToolTip(
            "Specify browser profile if you have multiple profiles."
        )
        self.profile_input.textChanged.connect(self._save_settings)
        profile_row.addWidget(profile_label, 0)
        profile_row.addWidget(self.profile_input, 1)
        browser_group_layout.addLayout(profile_row)

        advanced_row = QHBoxLayout()
        keyring_label = QLabel("Keyring:", self)
        keyring_label.setToolTip(
            "Keyring backend (Linux only, optional). Usually not needed."
        )
        self.keyring_input = QLineEdit(self)
        self.keyring_input.setPlaceholderText("Optional: Keyring backend")
        self.keyring_input.setToolTip(
            "For Linux systems with custom keyring configurations."
        )
        self.keyring_input.textChanged.connect(self._save_settings)
        advanced_row.addWidget(keyring_label, 0)
        advanced_row.addWidget(self.keyring_input, 1)

        container_label = QLabel("Container:", self)
        container_label.setToolTip(
            "Firefox container name (optional). For Multi-Account Containers extension."
        )
        self.container_input = QLineEdit(self)
        self.container_input.setPlaceholderText("Optional: Firefox container")
        self.container_input.setToolTip(
            "Firefox Multi-Account Container name (e.g., 'Personal', 'Work')."
        )
        self.container_input.textChanged.connect(self._save_settings)
        advanced_row.addWidget(container_label, 0)
        advanced_row.addWidget(self.container_input, 1)
        browser_group_layout.addLayout(advanced_row)

        cookies_layout.addWidget(browser_group)

        # Cookie file fallback group
        file_group = QGroupBox("Cookie File (Fallback)", self)
        file_group_layout = QHBoxLayout(file_group)
        file_group_layout.setSpacing(6)

        cookie_file_label = QLabel("Cookie File:", self)
        cookie_file_label.setToolTip(
            "Path to a Netscape-format cookies.txt file. "
            "Used exclusively when 'Cookie File (Fallback)' is selected as the source."
        )
        self.cookie_file_input = QLineEdit(self)
        self.cookie_file_input.setPlaceholderText(
            "Path to cookies.txt (Netscape format)"
        )
        self.cookie_file_input.setToolTip(
            "Netscape-format cookie file exported from browser. "
            "Used exclusively when 'Cookie File (Fallback)' is selected above."
        )
        self.cookie_file_input.textChanged.connect(self._save_settings)
        self.cookie_file_browse = QToolButton(self)
        self.cookie_file_browse.setObjectName("CookieBrowseButton")
        self.cookie_file_browse.setIcon(line_icon("file"))
        self.cookie_file_browse.setToolTip("Browse for cookie file")
        self.cookie_file_browse.clicked.connect(self._choose_cookie_file)
        file_group_layout.addWidget(cookie_file_label, 0)
        file_group_layout.addWidget(self.cookie_file_input, 1)
        file_group_layout.addWidget(self.cookie_file_browse, 0)

        cookies_layout.addWidget(file_group)

        # Help row with tip and help button
        help_row = QHBoxLayout()
        info_label = QLabel(
            "<b>Tip:</b> Browser cookies allow downloading age-restricted or premium content you have access to. "
            "Close the browser before downloading for best results.",
            self,
        )
        info_label.setObjectName("CookieTip")
        info_label.setWordWrap(True)
        help_row.addWidget(info_label, 1)

        self.help_button = QToolButton(self)
        self.help_button.setObjectName("HelpButton")
        self.help_button.setText("?")
        self.help_button.setToolTip("Open Cookie Help Guide")
        self.help_button.setAccessibleName("Open Cookie Help Guide")
        self.help_button.clicked.connect(self._show_cookie_help)
        help_row.addWidget(self.help_button, 0)

        cookies_layout.addLayout(help_row)

        cookies_layout.addStretch(1)
        self.tabs.addTab(cookies_tab, "Cookies")

        # Progress, status, and log remain outside tabs (always visible)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar, 0)

        self.status_label = QLabel("Ready", self)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setProperty("state", "ready")
        self.status_label.setAccessibleName("Download status")
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label, 0)

        self.log_output = QPlainTextEdit(self)
        self.log_output.setObjectName("LogOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setAccessibleName("Download activity log")
        self.log_output.setMinimumHeight(104)
        self.log_output.setPlaceholderText("Status and activity will appear here.")
        self.log_output.setToolTip(
            "Toolchain, network, download status, progress, and error output."
        )
        root.addWidget(self.log_output, 1)

        self.setCentralWidget(central)

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
        self.dir_input.textChanged.connect(self._save_settings)
        self.mp3_btn.toggled.connect(self._save_settings)
        self.mp4_btn.toggled.connect(self._save_settings)

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._start_downloads)
        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.url_input.setFocus)
        QShortcut(QKeySequence("Esc"), self, activated=self._cancel_downloads)

        self.mp3_btn.setChecked(True)
        self._update_quality_options()
        self._refresh_dependency_status()
        self._update_queue_summary()
        self._set_status("Ready")

        self.setMinimumSize(760, 600)
        self.resize(920, 700)

        self._check_network_status()

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
        """Keep the compatibility label in sync while rendering status in the console."""
        self.status_label.setText(message)
        self._set_widget_state(self.status_label, state)
        if not hasattr(self, "log_output"):
            return
        if live:
            self._set_live_console_status(f"Status: {message}")
        else:
            self.append_log(f"Status: {message}")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:
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
        if self.browser_combo.findText(browser) < 0:
            browser = "None"
        # Legacy configs saved a cookie file while the source was 'None' and the
        # file was still sent. Keep those downloads working: switch to the file source.
        if browser == "None" and cookie_file:
            browser = self.COOKIE_FILE_SOURCE
        self.browser_combo.setCurrentIndex(self.browser_combo.findText(browser))

        self.profile_input.setText(self.settings.value("cookie_profile", "", type=str))
        self.keyring_input.setText(self.settings.value("cookie_keyring", "", type=str))
        self.container_input.setText(
            self.settings.value("cookie_container", "", type=str)
        )
        self.cookie_file_input.setText(cookie_file)
        self._update_browser_fields(self.browser_combo.currentText())

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
        self.settings.setValue("cookie_browser", self.browser_combo.currentText())
        self.settings.setValue("cookie_profile", self.profile_input.text())
        self.settings.setValue("cookie_keyring", self.keyring_input.text())
        self.settings.setValue("cookie_container", self.container_input.text())
        self.settings.setValue("cookie_file", self.cookie_file_input.text())

    def _apply_template_preset(self) -> None:
        preset_text = self.template_presets.currentText()
        current = self.template_line.text().strip()
        if (
            current
            in [
                self.template_presets.itemText(i)
                for i in range(self.template_presets.count())
            ]
            or not current
        ):
            self.template_line.setText(preset_text)
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
        analysis = self._get_queue_analysis()
        count = len(analysis.urls)
        noun = "link" if count == 1 else "links"
        summary_parts = [f"Queue: {count} {noun}"]
        tooltip_parts = [f"{count} unique download {noun} ready."]

        if analysis.duplicate_count:
            duplicate_noun = (
                "duplicate" if analysis.duplicate_count == 1 else "duplicates"
            )
            summary_parts.append(f"{analysis.duplicate_count} {duplicate_noun}")
            tooltip_parts.append("Duplicate links are skipped when downloading.")

        if analysis.invalid_entries:
            invalid_count = len(analysis.invalid_entries)
            summary_parts.append(f"{invalid_count} invalid")
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
            summary_parts.append(f"{analysis.comment_count} ignored")
            tooltip_parts.append(
                f"{analysis.comment_count} comment {ignored_noun} will be ignored."
            )

        self.queue_label.setText(" · ".join(summary_parts))
        self.queue_label.setToolTip("\n".join(tooltip_parts))
        if analysis.invalid_entries:
            state = "warning"
        elif analysis.duplicate_count or analysis.comment_count:
            state = "notice"
        else:
            state = "ready"
        if self.queue_label.property("state") != state:
            self.queue_label.setProperty("state", state)
            self.queue_label.style().unpolish(self.queue_label)
            self.queue_label.style().polish(self.queue_label)
        self.clean_urls_button.setEnabled(
            analysis.has_cleanup_items and self.url_input.isEnabled()
        )

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
        self.dependency_label.setText(toolchain_text)
        if (
            hasattr(self, "log_output")
            and toolchain_text != self._last_toolchain_console_text
        ):
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
            if self.browser_combo.currentText() == "None":
                self.browser_combo.setCurrentText(self.COOKIE_FILE_SOURCE)

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
        browser = self.browser_combo.currentText()
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
        browser = self.browser_combo.currentText()
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
        dialog.setWindowTitle("Cookie Fetching Help")
        dialog.setMinimumSize(550, 450)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("<h2>🍪 Cookie Fetching Guide</h2>", dialog)
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        help_text = QTextBrowser(dialog)
        help_text.setOpenExternalLinks(True)
        help_text.setHtml("""
        <style>
            body { color: #f1f4f8; font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; }
            h3 { color: #a78bfa; margin-top: 16px; margin-bottom: 8px; }
            p { margin: 6px 0; line-height: 1.5; }
            ul { margin-left: 20px; }
            li { margin: 4px 0; }
            code { background-color: #242a34; padding: 2px 6px; border-radius: 3px; color: #a8e7c2; }
            .warning { color: #f3bd63; }
            .browser { color: #c4b5fd; }
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
        
        <p style="margin-top: 20px; color: #888;">
            For more info, see: 
            <a href="https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp" style="color: #a78bfa;">yt-dlp Cookie FAQ</a>
        </p>
        """)
        layout.addWidget(help_text, 1)

        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setFixedWidth(100)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

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
        self.start_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)
        self.pause_button.setEnabled(not enabled)
        self.skip_button.setEnabled(not enabled)

    def _check_network_status(self) -> None:
        """Start a cancellable, non-blocking TCP connectivity check."""
        self._cancel_network_check()
        self.network_label.setText("Network: Checking...")
        self._set_widget_state(self.network_label, "pending")
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
        if is_online:
            self.network_label.setText(f"Network: Online | yt-dlp: {ytdlp_ver}")
            self._set_widget_state(self.network_label, "ready")
            self.append_log(f"Network status: Online | yt-dlp: {ytdlp_ver}")
        else:
            self.network_label.setText(f"Network: Offline | yt-dlp: {ytdlp_ver}")
            self._set_widget_state(self.network_label, "error")
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
            self.pause_button.setText("Pause")
            self.pause_button.setToolTip("Pause the current download")
            self.append_log("Download resumed")
        else:
            worker.pause()
            self.pause_button.setText("Resume")
            self.pause_button.setToolTip("Resume the paused download")
            self.append_log("Download paused")

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
            return "Please enter at least one URL (one per line)."
        directory = self.dir_input.text().strip()
        if not directory:
            return "Please choose a download directory."
        if self.aria2c_checkbox.isChecked() and not self._aria2c_available:
            return (
                "aria2c is enabled but aria2c.exe was not found.\n"
                "Place aria2c.exe beside YTDLE.exe, keep it in the project folder when running from source, "
                "or disable Use aria2c."
            )
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            return f"Cannot create directory:\n{directory}\n{e}"
        return None

    def _start_downloads(self) -> None:
        error = self._validate_inputs()
        if error:
            QMessageBox.warning(self, "Validation", error)
            self._set_status(error, "error")
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
        self.progress_bar.setValue(0)
        self._set_status("Starting download...", "active")
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
        self.progress_bar.setValue(max(0, min(100, value)))

    def _on_status(self, text: str) -> None:
        prefix = ""
        if self._downloading_total:
            prefix = (
                f"Completed {self._downloading_completed}/{self._downloading_total}"
                f" | Active {self._downloading_active}: "
            )
        self._set_status(prefix + text, "active", live=True)

    def _on_item_started(self, url: str) -> None:
        self._downloading_started += 1
        self._downloading_active += 1
        self.append_log(
            f"Starting {self._downloading_started}/{self._downloading_total}: {url}"
        )

    def _on_item_finished(self, url: str, success: bool, info: str) -> None:
        self._downloading_active = max(0, self._downloading_active - 1)
        self._downloading_completed += 1
        if success:
            self.append_log(f"SUCCESS: {url}\nSaved to: {info}")
        else:
            self.append_log(f"FAILED: {url}\nReason: {info}")

    def _on_all_finished(self, success_count: int, fail_count: int) -> None:
        self.append_log(f"All done. Success: {success_count}, Failed: {fail_count}")
        if fail_count > 0:
            self._set_status(
                f"Completed with errors. Success: {success_count}, Failed: {fail_count}",
                "warning",
            )
        else:
            self._set_status(
                f"Completed successfully. Items: {success_count}", "ready"
            )

        self._set_controls_enabled(True)

        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()

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
