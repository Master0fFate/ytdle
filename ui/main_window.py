import os
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, QSettings
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QStyle,
    QPlainTextEdit,
    QPushButton,
    QButtonGroup,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QTabWidget,
    QGroupBox,
    QDialog,
    QTextBrowser,
)

from core.config import DownloadOptions
from core.downloader import VideoDownloadWorker
from core.async_manager import AsyncVideoDownloadWorker
from core.dependencies import check_dependencies
from core.utils import open_in_file_manager
from core.history import DownloadHistory
from ui.components.title_bar import CustomTitleBar
from ui.components import HistoryDialog


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
        
        deps = check_dependencies()
        self._ffmpeg_path = deps["ffmpeg"]
        self._yt_dlp_version = deps["yt_dlp"]
        self._ffmpeg_available: bool = self._ffmpeg_path != "Not found"
        
        self._downloading_total: int = 0
        self._downloading_index: int = 0

        self.settings = QSettings("Merlin", "YTDLE_v2")

        self._init_ui()
        self._load_settings()
        self.setAcceptDrops(True)

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

        # === Download Tab ===
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
        self.browse_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.browse_button.setToolTip("Choose download directory")
        self.browse_button.clicked.connect(self._choose_directory)
        dir_row.addWidget(self.browse_button, 0)

        self.open_folder_button = QToolButton(self)
        self.open_folder_button.setObjectName("OpenFolderButton")
        self.open_folder_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.open_folder_button.setToolTip("Open the current download folder in your file manager")
        self.open_folder_button.clicked.connect(self._open_folder)
        dir_row.addWidget(self.open_folder_button, 0)

        download_layout.addLayout(dir_row)

        url_label = QLabel("URLs:", self)
        url_label.setToolTip("Paste one URL per line. You can also drag & drop links here.")
        download_layout.addWidget(url_label, 0)
        self.url_input = QPlainTextEdit(self)
        self.url_input.setPlaceholderText("Enter one URL per line (YouTube, Twitter, TikTok, etc.)")
        self.url_input.setTabChangesFocus(True)
        self.url_input.setMinimumHeight(96)
        self.url_input.setToolTip("Paste one URL per line. You can also drag & drop links here.")
        download_layout.addWidget(self.url_input, 1)

        fmt_row = QHBoxLayout()

        fmt_label = QLabel("Format:", self)
        fmt_label.setToolTip("Choose MP3 for audio-only, or MP4 for full video.")
        fmt_row.setSpacing(6)
        fmt_row.addWidget(fmt_label, 0)

        self.mp3_btn = QPushButton("MP3", self)
        self.mp3_btn.setCheckable(True)
        self.mp3_btn.setProperty("formatToggle", True)
        self.mp3_btn.setToolTip("Audio-only download. Converts best audio to MP3 at the selected bitrate.")

        self.mp4_btn = QPushButton("MP4", self)
        self.mp4_btn.setCheckable(True)
        self.mp4_btn.setProperty("formatToggle", True)
        self.mp4_btn.setToolTip("Video download (MP4). Respects the maximum resolution you select.")

        self.fmt_group = QButtonGroup(self)
        self.fmt_group.setExclusive(True)
        self.fmt_group.addButton(self.mp3_btn)
        self.fmt_group.addButton(self.mp4_btn)

        fmt_row.addWidget(self.mp3_btn, 0)
        fmt_row.addWidget(self.mp4_btn, 0)

        fmt_row.addSpacing(12)

        qual_label = QLabel("Quality:", self)
        qual_label.setToolTip("MP3: bitrate (kbps). MP4: maximum video resolution. 'Best' picks the highest available.")
        fmt_row.addWidget(qual_label, 0)

        self.quality_combo = QComboBox(self)
        self.quality_combo.setToolTip("Select bitrate for MP3, or resolution cap for MP4.")
        fmt_row.addWidget(self.quality_combo, 0)

        fmt_row.addStretch(1)
        download_layout.addLayout(fmt_row)

        tmpl_row = QHBoxLayout()
        tmpl_label = QLabel("Output template:", self)
        tmpl_label.setToolTip("Naming pattern (yt_dlp template). The file extension is added automatically.")
        tmpl_row.setSpacing(6)
        tmpl_row.addWidget(tmpl_label, 0)

        self.template_presets = QComboBox(self)
        self.template_presets.addItems([
            "%(title).150s",
            "%(uploader)s - %(title).150s",
            "%(playlist_title)s/%(playlist_index)03d - %(title).150s",
            "%(channel)s/%(upload_date)s - %(title).100s",
        ])
        self.template_presets.setToolTip("Pick a common naming pattern for file names/folders.")
        tmpl_row.addWidget(self.template_presets, 0)

        self.template_line = QLineEdit(self)
        self.template_line.setPlaceholderText("%(title).150s")
        self.template_line.setToolTip("Freeform yt_dlp output template (no extension). Example: %(uploader)s - %(title).150s")
        tmpl_row.addWidget(self.template_line, 1)
        download_layout.addLayout(tmpl_row)

        ffmpeg_row = QHBoxLayout()
        ffmpeg_label = QLabel("FFmpeg Args:", self)
        ffmpeg_label.setToolTip("Custom FFmpeg arguments (e.g. -vcodec libx264). Optional.")
        ffmpeg_row.setSpacing(6)
        ffmpeg_row.addWidget(ffmpeg_label, 0)
        
        self.ffmpeg_input = QLineEdit(self)
        self.ffmpeg_input.setPlaceholderText("Optional: Custom FFmpeg args (e.g. -vcodec libx264)")
        self.ffmpeg_input.setToolTip("Pass extra arguments to FFmpeg post-processor.")
        ffmpeg_row.addWidget(self.ffmpeg_input, 1)

        self.ffmpeg_mode = QComboBox(self)
        self.ffmpeg_mode.addItems(["Append", "Override"])
        self.ffmpeg_mode.setToolTip("Append: Add to defaults. Override: Replace/Force specific args.")
        self.ffmpeg_mode.setFixedWidth(100)
        ffmpeg_row.addWidget(self.ffmpeg_mode, 0)
        
        download_layout.addLayout(ffmpeg_row)

        opt_row = QHBoxLayout()
        self.playlist_checkbox = QCheckBox("Download playlist", self)
        self.playlist_checkbox.setToolTip("If the link is a playlist/series, download all items. Otherwise only the single video.")
        self.restrict_checkbox = QCheckBox("Restrict filenames", self)
        self.restrict_checkbox.setToolTip("Use only ASCII-safe characters in file names (helps on some filesystems).")
        self.async_checkbox = QCheckBox("Async mode", self)
        self.async_checkbox.setToolTip("Use async download manager for better concurrency and performance")
        self.async_checkbox.setChecked(True)
        self.aria2c_checkbox = QCheckBox("Use aria2c", self)
        self.aria2c_checkbox.setToolTip("Use aria2c for multi-connection downloads (faster but requires aria2c binary)")
        opt_row.addWidget(self.playlist_checkbox, 0)
        opt_row.addWidget(self.restrict_checkbox, 0)
        opt_row.addWidget(self.async_checkbox, 0)
        opt_row.addWidget(self.aria2c_checkbox, 0)
        opt_row.addStretch(1)
        opt_row.setSpacing(6)
        download_layout.addLayout(opt_row)

        actions_row = QHBoxLayout()
        self.history_button = QPushButton("History", self)
        self.history_button.setObjectName("HistoryButton")
        self.history_button.setToolTip("View download history and manage failed downloads")
        self.history_button.clicked.connect(self._show_history_dialog)
        
        self.network_label = QLabel("Network: Checking...", self)
        self.network_label.setObjectName("NetworkLabel")
        self.network_label.setToolTip("Current network connection status")
        
        self.check_network_button = QPushButton("Check Network", self)
        self.check_network_button.setObjectName("CheckNetworkButton")
        self.check_network_button.setToolTip("Manually check internet connection")
        self.check_network_button.clicked.connect(self._check_network_status)
        
        actions_row.addWidget(self.history_button, 0)
        actions_row.addWidget(self.network_label, 0)
        actions_row.addWidget(self.check_network_button, 0)
        actions_row.addStretch(1)
        
        self.start_button = QPushButton("Start Download", self)
        self.start_button.setObjectName("DownloadButton")
        self.start_button.setToolTip("Start downloading all URLs in the list")
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setToolTip("Request a safe stop after the current file finishes processing")
        self.cancel_button.setEnabled(False)
        self.pause_button = QPushButton("Pause", self)
        self.pause_button.setObjectName("PauseButton")
        self.pause_button.setToolTip("Pause the current download")
        self.pause_button.setEnabled(False)
        self.skip_button = QPushButton("Skip", self)
        self.skip_button.setObjectName("SkipButton")
        self.skip_button.setToolTip("Skip the current download and move to the next")
        self.skip_button.setEnabled(False)
        actions_row.addWidget(self.start_button, 0)
        actions_row.addWidget(self.cancel_button, 0)
        actions_row.addWidget(self.pause_button, 0)
        actions_row.addWidget(self.skip_button, 0)
        actions_row.setSpacing(6)
        download_layout.addLayout(actions_row)

        self.tabs.addTab(download_tab, "Download")

        # === Cookies Tab ===
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
        browser_label.setToolTip("Select browser to fetch cookies from. Only officially supported browsers work.")
        self.browser_combo = QComboBox(self)
        self.browser_combo.addItems([
            "None",
            "brave",
            "chrome",
            "chromium",
            "edge",
            "firefox",
            "opera",
            "safari",
            "vivaldi",
        ])
        self.browser_combo.setToolTip(
            "Select browser to extract cookies from.\n"
            "For Chromium forks (Thorium, Ungoogled, etc.), use Cookie File instead."
        )
        self.browser_combo.currentTextChanged.connect(self._on_browser_changed)
        browser_row.addWidget(browser_label, 0)
        browser_row.addWidget(self.browser_combo, 1)
        browser_group_layout.addLayout(browser_row)

        profile_row = QHBoxLayout()
        profile_label = QLabel("Profile:", self)
        profile_label.setToolTip("Browser profile name (optional). Leave empty for default profile.")
        self.profile_input = QLineEdit(self)
        self.profile_input.setPlaceholderText("Optional: Browser profile name (e.g., 'Default', 'Profile 1')")
        self.profile_input.setToolTip("Specify browser profile if you have multiple profiles.")
        self.profile_input.textChanged.connect(self._save_settings)
        profile_row.addWidget(profile_label, 0)
        profile_row.addWidget(self.profile_input, 1)
        browser_group_layout.addLayout(profile_row)

        advanced_row = QHBoxLayout()
        keyring_label = QLabel("Keyring:", self)
        keyring_label.setToolTip("Keyring backend (Linux only, optional). Usually not needed.")
        self.keyring_input = QLineEdit(self)
        self.keyring_input.setPlaceholderText("Optional: Keyring backend")
        self.keyring_input.setToolTip("For Linux systems with custom keyring configurations.")
        self.keyring_input.textChanged.connect(self._save_settings)
        advanced_row.addWidget(keyring_label, 0)
        advanced_row.addWidget(self.keyring_input, 1)

        container_label = QLabel("Container:", self)
        container_label.setToolTip("Firefox container name (optional). For Multi-Account Containers extension.")
        self.container_input = QLineEdit(self)
        self.container_input.setPlaceholderText("Optional: Firefox container")
        self.container_input.setToolTip("Firefox Multi-Account Container name (e.g., 'Personal', 'Work').")
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
        cookie_file_label.setToolTip("Path to a Netscape-format cookies.txt file. Used if browser cookies are disabled.")
        self.cookie_file_input = QLineEdit(self)
        self.cookie_file_input.setPlaceholderText("Path to cookies.txt (Netscape format)")
        self.cookie_file_input.setToolTip("Netscape-format cookie file exported from browser.")
        self.cookie_file_input.textChanged.connect(self._save_settings)
        self.cookie_file_browse = QToolButton(self)
        self.cookie_file_browse.setObjectName("CookieBrowseButton")
        self.cookie_file_browse.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
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
            self
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        help_row.addWidget(info_label, 1)

        self.help_button = QToolButton(self)
        self.help_button.setObjectName("HelpButton")
        self.help_button.setText("?")
        self.help_button.setToolTip("Open Cookie Help Guide")
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
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label, 0)

        self.log_output = QPlainTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)
        self.log_output.setToolTip("Detailed log of actions, options, progress, and errors.")
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

        self.mp3_btn.setChecked(True)
        self._update_quality_options()

        self.setMinimumSize(700, 560)

        self._check_network_status()

    # --------------- Drag & Drop ---------------
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
        if event.mimeData().hasText():
            txt = event.mimeData().text()
            if txt:
                text_parts.extend(line.strip() for line in txt.splitlines())
        urls = [t for t in (part.strip() for part in text_parts) if t]
        if urls:
            current = self.url_input.toPlainText().strip()
            joined = "\\n".join(urls)
            self.url_input.setPlainText((current + "\\n" + joined).strip() if current else joined)
            self.append_log(f"Added {len(urls)} URL(s) via drag & drop.")
        event.acceptProposedAction()

    # --------------- Settings ---------------
    def _default_download_dir(self) -> str:
        root_dir = os.path.expanduser("~")
        return os.path.join(root_dir, "YTDLE")

    def _load_settings(self) -> None:
        directory = self.settings.value("directory", self._default_download_dir(), type=str)
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
        browser = self.settings.value("cookie_browser", "None", type=str)
        browser_idx = self.browser_combo.findText(browser)
        if browser_idx >= 0:
            self.browser_combo.setCurrentIndex(browser_idx)
        
        profile = self.settings.value("cookie_profile", "", type=str)
        self.profile_input.setText(profile)
        
        keyring = self.settings.value("cookie_keyring", "", type=str)
        self.keyring_input.setText(keyring)
        
        container = self.settings.value("cookie_container", "", type=str)
        self.container_input.setText(container)
        
        cookie_file = self.settings.value("cookie_file", "", type=str)
        self.cookie_file_input.setText(cookie_file)

    def _save_settings(self) -> None:
        self.settings.setValue("directory", self.dir_input.text().strip())
        is_mp3 = self.mp3_btn.isChecked()
        self.settings.setValue("is_mp3", is_mp3)
        self.settings.setValue("quality", self.quality_combo.currentText())
        self.settings.setValue("download_playlist", self.playlist_checkbox.isChecked())
        self.settings.setValue("restrict_filenames", self.restrict_checkbox.isChecked())
        self.settings.setValue("use_async", self.async_checkbox.isChecked())
        self.settings.setValue("use_aria2c", self.aria2c_checkbox.isChecked())
        self.settings.setValue("template_preset_index", self.template_presets.currentIndex())
        self.settings.setValue("outtmpl_template", self.template_line.text())
        self.settings.setValue("ffmpeg_args", self.ffmpeg_input.text())
        self.settings.setValue("ffmpeg_mode", self.ffmpeg_mode.currentText())
        
        # Cookie settings
        self.settings.setValue("cookie_browser", self.browser_combo.currentText())
        self.settings.setValue("cookie_profile", self.profile_input.text())
        self.settings.setValue("cookie_keyring", self.keyring_input.text())
        self.settings.setValue("cookie_container", self.container_input.text())
        self.settings.setValue("cookie_file", self.cookie_file_input.text())

    # --------------- UI helpers ---------------
    def _apply_template_preset(self) -> None:
        preset_text = self.template_presets.currentText()
        current = self.template_line.text().strip()
        if current in [self.template_presets.itemText(i) for i in range(self.template_presets.count())] or not current:
            self.template_line.setText(preset_text)
        self._save_settings()

    def _update_quality_options(self) -> None:
        self.quality_combo.clear()
        if self.mp3_btn.isChecked():
            self.quality_combo.addItems(["320k", "256k", "192k", "128k"])
        else:
            self.quality_combo.addItems(["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"])
        self._save_settings()

    def _choose_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.dir_input.text())
        if path:
            self.dir_input.setText(os.path.normpath(path))

    def _open_folder(self) -> None:
        open_in_file_manager(self.dir_input.text().strip())

    def _on_browser_changed(self, browser: str) -> None:
        """Save settings when browser changes."""
        self._save_settings()

    def _choose_cookie_file(self) -> None:
        """Open file dialog to select a cookie file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookie File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.cookie_file_input.setText(os.path.normpath(path))

    def _get_cookies_from_browser_tuple(self):
        """Build the cookies_from_browser tuple for yt-dlp."""
        browser = self.browser_combo.currentText()
        if browser == "None":
            return None
        
        profile = self.profile_input.text().strip() or None
        keyring = self.keyring_input.text().strip() or None
        container = self.container_input.text().strip() or None
        
        return (browser, profile, keyring, container)

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
        title.setStyleSheet("color: #0a84ff; font-size: 16px;")
        layout.addWidget(title)
        
        help_text = QTextBrowser(dialog)
        help_text.setOpenExternalLinks(True)
        help_text.setHtml("""
        <style>
            body { color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; }
            h3 { color: #0a84ff; margin-top: 16px; margin-bottom: 8px; }
            p { margin: 6px 0; line-height: 1.5; }
            ul { margin-left: 20px; }
            li { margin: 4px 0; }
            code { background-color: #2a2a2a; padding: 2px 6px; border-radius: 3px; color: #4caf50; }
            .warning { color: #ff9800; }
            .browser { color: #4fc3f7; }
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
            <li>Please use the <b>Cookie File</b> method below.</li>
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
        
        <h3>Cookie File (Alternative)</h3>
        <p>If browser cookies don't work, you can export cookies manually:</p>
        <ul>
            <li>Use a browser extension like "Get cookies.txt LOCALLY"</li>
            <li>Export to Netscape format (.txt file)</li>
            <li>Select the file in the "Cookie File (Fallback)" section</li>
        </ul>
        
        <p style="margin-top: 20px; color: #888;">
            For more info, see: 
            <a href="https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp" style="color: #0a84ff;">yt-dlp Cookie FAQ</a>
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
                current = self.url_input.toPlainText().strip()
                joined = "\\n".join(retry_urls)
                self.url_input.setPlainText((current + "\\n" + joined).strip() if current else joined)
                self.append_log(f"Added {len(retry_urls)} URL(s) from history to download queue.")

    def append_log(self, message: str) -> None:
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
        self.history_button.setEnabled(True)
        self.check_network_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)
        self.pause_button.setEnabled(not enabled)
        self.skip_button.setEnabled(not enabled)

    def _check_network_status(self) -> None:
        self.network_label.setText("Network: Checking...")
        self.network_label.setStyleSheet("")

        from core.network import check_internet_connection
        is_online = check_internet_connection()

        if is_online:
            self.network_label.setText("Network: Online")
            self.network_label.setStyleSheet("color: #4caf50;")
            self.append_log("Network status: Online")
        else:
            self.network_label.setText("Network: Offline")
            self.network_label.setStyleSheet("color: #f44336;")
            self.append_log("Network status: Offline - downloads may fail")

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

    # --------------- Validation ---------------
    def _collect_urls(self) -> List[str]:
        text = self.url_input.toPlainText()
        lines = [ln.strip() for ln in text.splitlines()]
        urls = [ln for ln in lines if ln]
        return urls

    def _validate_inputs(self) -> Optional[str]:
        urls = self._collect_urls()
        if not urls:
            return "Please enter at least one URL (one per line)."
        directory = self.dir_input.text().strip()
        if not directory:
            return "Please choose a download directory."
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            return f"Cannot create directory:\\n{directory}\\n{e}"
        return None

    # --------------- Download lifecycle ---------------
    def _start_downloads(self) -> None:
        error = self._validate_inputs()
        if error:
            QMessageBox.warning(self, "Validation", error)
            self.status_label.setText(error)
            return

        urls = self._collect_urls()
        self._downloading_total = len(urls)
        self._downloading_index = 0

        # Determine ffmpeg args based on mode
        f_args = self.ffmpeg_input.text().strip()
        f_mode = self.ffmpeg_mode.currentText()

        f_add = f_args if f_mode == "Append" else None
        f_override = f_args if f_mode == "Override" else None

        # Determine if using async mode
        use_async = self.async_checkbox.isChecked()
        use_aria2c = self.aria2c_checkbox.isChecked()

        opts = DownloadOptions(
            is_mp3=self.mp3_btn.isChecked(),
            quality=self.quality_combo.currentText(),
            outtmpl_template=self.template_line.text(),
            directory=self.dir_input.text().strip(),
            download_playlist=self.playlist_checkbox.isChecked(),
            restrict_filenames=self.restrict_checkbox.isChecked(),
            ffmpeg_add_args=f_add,
            ffmpeg_override_args=f_override,
            cookies_from_browser=self._get_cookies_from_browser_tuple(),
            cookies=self.cookie_file_input.text().strip() or None,
            use_aria2c=use_aria2c,
            max_connections=16,
            max_concurrent_downloads=3,
        )

        self._set_controls_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")
        self.append_log(f"System: yt-dlp {self._yt_dlp_version}, ffmpeg: {self._ffmpeg_path}")
        self.append_log(f"Queue size: {len(urls)}")
        self.append_log(f"Format: {'MP3' if opts.is_mp3 else 'MP4'} | Quality: {opts.quality}")
        self.append_log(f"Output dir: {opts.directory}")
        self.append_log(f"Template: {opts.outtmpl_template}.%(ext)s")
        self.append_log(f"Playlist: {'Yes' if opts.download_playlist else 'No'} | Restrict filenames: {'Yes' if opts.restrict_filenames else 'No'}")
        self.append_log(f"Async mode: {'Yes' if use_async else 'No'} | Aria2c: {'Yes' if use_aria2c else 'No'}")
        if not self._ffmpeg_available:
            self.append_log("Warning: ffmpeg not found on PATH. Audio extraction and metadata embedding may fail.")

        if use_async:
            # Use async download manager
            self._worker_thread = QThread(self)
            self._async_worker = AsyncVideoDownloadWorker(urls, opts, history=self._history, max_concurrent=3)
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
            # Use legacy sync download manager
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
            self.append_log("Cancellation requested...")
            self.status_label.setText("Cancelling...")
            self.cancel_button.setEnabled(False)
            worker.cancel()

    def _skip_current(self) -> None:
        worker = self._worker or self._async_worker
        if worker:
            self.append_log("Skipping current download...")
            self.status_label.setText("Skipping...")
            self.skip_button.setEnabled(False)
            worker.skip_current()

    def _on_progress(self, value: int) -> None:
        self.progress_bar.setValue(max(0, min(100, value)))

    def _on_status(self, text: str) -> None:
        prefix = f"Item {self._downloading_index}/{self._downloading_total}: " if self._downloading_total else ""
        self.status_label.setText(prefix + text)

    def _on_item_started(self, url: str) -> None:
        self._downloading_index += 1
        self.append_log(f"Starting {self._downloading_index}/{self._downloading_total}: {url}")

    def _on_item_finished(self, url: str, success: bool, info: str) -> None:
        if success:
            self.append_log(f"SUCCESS: {url}\\nSaved to: {info}")
        else:
            self.append_log(f"FAILED: {url}\\nReason: {info}")

    def _on_all_finished(self, success_count: int, fail_count: int) -> None:
        self.append_log(f"All done. Success: {success_count}, Failed: {fail_count}")
        if fail_count > 0:
            self.status_label.setText(f"Completed with errors. Success: {success_count}, Failed: {fail_count}")
        else:
            self.status_label.setText(f"Completed successfully. Items: {success_count}")

        self._set_controls_enabled(True)

        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()

    def _on_error(self, message: str) -> None:
        self.status_label.setText(message)

    def _cleanup_worker(self) -> None:
        if self._worker:
            try:
                self._worker.deleteLater()
            except Exception:
                pass
            self._worker = None
        if self._async_worker:
            try:
                self._async_worker.deleteLater()
            except Exception:
                pass
            self._async_worker = None
        if self._worker_thread:
            try:
                self._worker_thread.deleteLater()
            except Exception:
                pass
            self._worker_thread = None

    # --------------- FFmpeg warning ---------------
    def _warn_ffmpeg(self) -> None:
        self.status_label.setText("ffmpeg not found. Some formats may not process. Consider installing ffmpeg.")
        self.append_log("ffmpeg not found on PATH. Audio extraction (MP3) and metadata embedding require ffmpeg.")

    # --------------- Window close / cleanup ---------------
    def closeEvent(self, event) -> None:
        try:
            worker = self._worker or self._async_worker
            if worker:
                worker.cancel()
            if self._worker_thread and self._worker_thread.isRunning():
                self._worker_thread.quit()
                self._worker_thread.wait(5000)
        except Exception:
            pass
        super().closeEvent(event)
