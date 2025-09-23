#!/usr/bin/env python3

import os
import sys
import shutil
import threading
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import (
    Qt,
    QObject,
    QThread,
    Signal,
    QSettings,
    QPoint,
    QUrl,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QProgressBar,
    QHBoxLayout,
    QVBoxLayout,
    QButtonGroup,
    QStyle,
    QMessageBox,
)

import yt_dlp


STYLESHEET = """
QMainWindow#MainWindow {
    background-color: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    color: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 9pt;
}

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

QCheckBox { spacing: 4px; }
"""


@dataclass
class DownloadOptions:
    is_mp3: bool
    quality: str
    outtmpl_template: str
    directory: str
    download_playlist: bool
    restrict_filenames: bool
    retries: int = 10
    fragment_retries: int = 10
    concurrent_fragment_downloads: int = 3
    nocheckcertificate: bool = False


def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def open_in_file_manager(path: str) -> None:
    if not path:
        return
    if not os.path.exists(path):
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(path)))


def format_eta(eta: Optional[int]) -> str:
    if not eta:
        return ""
    try:
        total = int(eta)
        m, s = divmod(total, 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
    except Exception:
        return ""


def format_status(speed_bps: Optional[float], eta: Optional[int]) -> str:
    parts: List[str] = []
    if speed_bps:
        try:
            parts.append(f"{(float(speed_bps) / (1024 * 1024)):.1f} MB/s")
        except Exception:
            pass
    if eta:
        eta_str = format_eta(eta)
        if eta_str:
            parts.append(f"ETA {eta_str}")
    if not parts:
        return "Downloading..."
    return "Downloading... " + " | ".join(parts)


def sanitize_template(template: str) -> str:
    t = (template or "").strip()
    return t or "%(title).150s"


def build_yt_dlp_options(opts: DownloadOptions, progress_hook: Callable, attempt: int = 0) -> Dict:
    outtmpl = os.path.join(opts.directory, f"{sanitize_template(opts.outtmpl_template)}.%(ext)s")

    base: Dict = {
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "quiet": False,
        "verbose": False,
        "retries": opts.retries,
        "fragment_retries": opts.fragment_retries,
        "noplaylist": not opts.download_playlist,
        "restrictfilenames": opts.restrict_filenames,
        "ignoreerrors": False,
        "noprogress": False,
        "concurrent_fragment_downloads": opts.concurrent_fragment_downloads,
        "nocheckcertificate": opts.nocheckcertificate,
        "prefer_ffmpeg": True,
    }

    if opts.is_mp3:
        bitrate = "".join(filter(str.isdigit, opts.quality)) or "192"
        base.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
        })
    else:
        # Progressive fallback for MP4 formats
        if attempt == 0:
            # First attempt: Try with specific codec requirements
            if opts.quality.lower() == "best":
                fmt = "bv*+ba/best"  # More flexible than requiring specific codecs
            else:
                try:
                    h = int("".join(filter(str.isdigit, opts.quality)))
                except ValueError:
                    h = 1080
                fmt = f"bv*[height<={h}]+ba/b[height<={h}]/best[height<={h}]/best"
        elif attempt == 1:
            # Second attempt: Simple height-based format without codec requirements
            if opts.quality.lower() == "best":
                fmt = "best[ext=mp4]/best"
            else:
                try:
                    h = int("".join(filter(str.isdigit, opts.quality)))
                except ValueError:
                    h = 1080
                fmt = f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
        else:
            # Final fallback: Just use best available
            fmt = "best"
            
        base.update({
            "format": fmt,
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata"}],
        })

    return base


class VideoDownloadWorker(QObject):
    progress = Signal(int)
    status = Signal(str)
    itemStarted = Signal(str)
    itemFinished = Signal(str, bool, str)
    allFinished = Signal(int, int)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, urls: List[str], options: DownloadOptions):
        super().__init__()
        self.urls = urls
        self.options = options
        self._cancel_event = threading.Event()
        self._current_output_file: Optional[str] = None
        self._last_logged_pct: int = -10
        self._artifact_candidates: set = set()
        self._last_item_dir: Optional[str] = None
        self._last_item_stem: Optional[str] = None

    def cancel(self) -> None:
        self._cancel_event.set()

    def _progress_hook(self, d: Dict) -> None:
        if self._cancel_event.is_set():
            raise RuntimeError("User cancelled")

        try:
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                pct = 0
                if total:
                    pct = int(downloaded * 100 / total)
                    self.progress.emit(pct)

                speed = d.get("speed")
                eta = d.get("eta")
                self.status.emit(format_status(speed, eta))

                if total and pct >= self._last_logged_pct + 10:
                    self._last_logged_pct = pct - (pct % 10)
                    self.log.emit(f"Progress: {pct}% | {format_status(speed, eta)}")

                filename = d.get("filename") or d.get("tmpfilename")
                if filename:
                    self._current_output_file = filename
                    try:
                        self._artifact_candidates.add(filename)
                        self._last_item_dir = os.path.dirname(filename) or self.options.directory
                        base = os.path.basename(filename)
                        self._last_item_stem = os.path.splitext(base)[0]
                    except Exception as _:
                        pass
                tmp = d.get("tmpfilename")
                if tmp:
                    try:
                        self._artifact_candidates.add(tmp)
                        if not self._last_item_dir:
                            self._last_item_dir = os.path.dirname(tmp) or self.options.directory
                        if not self._last_item_stem:
                            base = os.path.basename(tmp)
                            self._last_item_stem = os.path.splitext(base)[0]
                    except Exception as _:
                        pass

            elif status == "finished":
                self.status.emit("Processing downloaded file...")
                self.log.emit("Download finished. Running post-processing...")
                filename = d.get("filename") or self._current_output_file
                if filename:
                    self._current_output_file = filename
                    try:
                        self._artifact_candidates.add(filename)
                        self._last_item_dir = os.path.dirname(filename) or self.options.directory
                        base = os.path.basename(filename)
                        self._last_item_stem = os.path.splitext(base)[0]
                    except Exception as _:
                        pass
                self.progress.emit(100)
        except Exception as e:
            self.log.emit(f"Progress hook error: {e!r}")

    def _download_with_fallback(self, url: str) -> bool:
        max_attempts = 3 if not self.options.is_mp3 else 1
        
        for attempt in range(max_attempts):
            if self._cancel_event.is_set():
                raise RuntimeError("User cancelled")
                
            try:
                ydl_opts = build_yt_dlp_options(self.options, self._progress_hook, attempt)
                
                if attempt > 0:
                    self.log.emit(f"Retrying with fallback format (attempt {attempt + 1}/{max_attempts})")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Try to get video info first
                    try:
                        info = ydl.extract_info(url, download=False)
                        title = info.get("title") or "Unknown title"
                        uploader = info.get("uploader") or info.get("channel") or "Unknown"
                        dur = info.get("duration")
                        dur_str = format_eta(dur) if dur else "?"
                        self.log.emit(f"Info: {title} | Uploader: {uploader} | Duration: {dur_str}")
                    except Exception as ie:
                        self.log.emit(f"Info probe failed: {ie}")
                    
                    # Attempt download
                    ydl.download([url])
                    return True
                    
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a format error
                if "Requested format is not available" in error_str or "No video formats found" in error_str:
                    if attempt < max_attempts - 1:
                        self.log.emit(f"Format not available, trying fallback...")
                        continue
                    else:
                        self.log.emit(f"All format attempts failed for {url}")
                        raise
                        
                # For other errors, don't retry
                raise
                
        return False

    def _cleanup_artifacts_for_current_item(self) -> None:
        try:
            work_dir = self._last_item_dir or self.options.directory
            stem = self._last_item_stem
            candidates = set(self._artifact_candidates)
            if self._current_output_file:
                candidates.add(self._current_output_file)
                try:
                    tmp_dir = os.path.dirname(self._current_output_file)
                    tmp_base = os.path.basename(self._current_output_file)
                    stem = stem or os.path.splitext(tmp_base)[0]
                    work_dir = tmp_dir or work_dir
                except Exception:
                    pass

            if not work_dir:
                return

            patterns: List[str] = []
            if stem:
                patterns.extend([
                    f"{stem}.part",
                    f"{stem}.ytdl",
                    f"{stem}.ytdl.part",
                    f"{stem}.tmp",
                    f"{stem}.temp",
                    f"{stem}-video.*",
                    f"{stem}-audio.*",
                    f"{stem}*.m4s",
                    f"{stem}*.ts",
                    f"{stem}.webp",
                    f"{stem}.jpg",
                    f"{stem}.png",
                ])

            import glob
            for pat in patterns:
                try:
                    for p in glob.glob(os.path.join(work_dir, pat)):
                        candidates.add(p)
                except Exception:
                    pass

            removed = 0
            for path in list(candidates):
                try:
                    if not path:
                        continue
                    if not os.path.isabs(path):
                        path = os.path.join(work_dir, path)
                    if os.path.isfile(path):
                        os.remove(path)
                        removed += 1
                        self.log.emit(f"Cleanup: removed {path}")
                except Exception as e:
                    self.log.emit(f"Cleanup: failed to remove {path}: {e}")
            if removed == 0:
                self.log.emit("Cleanup: no artifacts found to remove")
        except Exception as e:
            self.log.emit(f"Cleanup error: {e}")

    def run(self) -> None:
        success_count, fail_count = 0, 0
        n = len(self.urls)

        ydl_ver = "unknown"
        try:
            from yt_dlp.version import __version__ as yv
            ydl_ver = yv
        except Exception:
            pass
        self.log.emit(f"yt-dlp version: {ydl_ver}")

        for idx, url in enumerate(self.urls, start=1):
            if self._cancel_event.is_set():
                self.log.emit("Cancellation requested. Stopping before next item.")
                break

            self._last_logged_pct = -10
            self._current_output_file = None
            self._artifact_candidates = set()
            self._last_item_dir = None
            self._last_item_stem = None
            self.itemStarted.emit(url)
            self.status.emit(f"Starting {idx}/{n}")
            self.progress.emit(0)
            self.log.emit(f"Preparing: {url}")

            try:
                os.makedirs(self.options.directory, exist_ok=True)
                
                # Try download with fallback
                if self._download_with_fallback(url):
                    success_count += 1
                    final_path = self._current_output_file or "Completed"
                    self.itemFinished.emit(url, True, final_path)
                    self.log.emit(f"Finished: {final_path}")
                else:
                    fail_count += 1
                    try:
                        self._cleanup_artifacts_for_current_item()
                    except Exception:
                        pass
                    self.itemFinished.emit(url, False, "Download failed after all attempts")
                    self.log.emit(f"Failed after all attempts: {url}")
                    
            except Exception as e:
                if str(e) == "User cancelled":
                    try:
                        self._cleanup_artifacts_for_current_item()
                    except Exception:
                        pass
                    self.itemFinished.emit(url, False, "Cancelled")
                    self.log.emit(f"Cancelled: {url}")
                    break
                fail_count += 1
                try:
                    self._cleanup_artifacts_for_current_item()
                except Exception:
                    pass
                msg = f"Error downloading {url}: {e}"
                self.error.emit(msg)
                self.itemFinished.emit(url, False, str(e))
                self.log.emit(msg)

        self.allFinished.emit(success_count, fail_count)


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self._drag_offset: Optional[QPoint] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.title_label = QLabel("YTDLE Media Downloader", self)
        layout.addWidget(self.title_label, 1)

        self.min_button = QToolButton(self)
        self.min_button.setObjectName("MinimizeButton")
        self.min_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        self.min_button.setToolTip("Minimize")
        self.min_button.clicked.connect(self._on_minimize)
        layout.addWidget(self.min_button, 0, Qt.AlignRight)

        self.close_button = QToolButton(self)
        self.close_button.setObjectName("CloseButton")
        self.close_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(self._on_close)
        layout.addWidget(self.close_button, 0, Qt.AlignRight)

        self.setLayout(layout)

    def _on_minimize(self) -> None:
        win = self.window()
        if win:
            win.showMinimized()

    def _on_close(self) -> None:
        win = self.window()
        if win:
            win.close()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self.window():
                pos = event.globalPosition().toPoint()
                self._drag_offset = pos - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (event.buttons() & Qt.LeftButton) and self._drag_offset is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.window().move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[VideoDownloadWorker] = None
        self._ffmpeg_available: bool = check_ffmpeg_available()
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

        root.addLayout(dir_row)

        url_label = QLabel("URLs:", self)
        url_label.setToolTip("Paste one URL per line. You can also drag & drop links here.")
        root.addWidget(url_label, 0)
        self.url_input = QPlainTextEdit(self)
        self.url_input.setPlaceholderText("Enter one URL per line (YouTube, Twitter, TikTok, etc.)")
        self.url_input.setTabChangesFocus(True)
        self.url_input.setMinimumHeight(96)
        self.url_input.setToolTip("Paste one URL per line. You can also drag & drop links here.")
        root.addWidget(self.url_input, 1)

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
        root.addLayout(fmt_row)

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
        root.addLayout(tmpl_row)

        opt_row = QHBoxLayout()
        self.playlist_checkbox = QCheckBox("Download playlist", self)
        self.playlist_checkbox.setToolTip("If the link is a playlist/series, download all items. Otherwise only the single video.")
        self.restrict_checkbox = QCheckBox("Restrict filenames", self)
        self.restrict_checkbox.setToolTip("Use only ASCII-safe characters in file names (helps on some filesystems).")
        opt_row.addWidget(self.playlist_checkbox, 0)
        opt_row.addWidget(self.restrict_checkbox, 0)
        opt_row.addStretch(1)
        opt_row.setSpacing(6)
        root.addLayout(opt_row)

        actions_row = QHBoxLayout()
        self.start_button = QPushButton("Start Download", self)
        self.start_button.setObjectName("DownloadButton")
        self.start_button.setToolTip("Start downloading all URLs in the list")
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setObjectName("CancelButton")
        self.cancel_button.setToolTip("Request a safe stop after the current file finishes processing")
        self.cancel_button.setEnabled(False)
        actions_row.addStretch(1)
        actions_row.addWidget(self.start_button, 0)
        actions_row.addWidget(self.cancel_button, 0)
        actions_row.setSpacing(6)
        root.addLayout(actions_row)

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
        self.mp3_btn.clicked.connect(self._update_quality_options)
        self.mp4_btn.clicked.connect(self._update_quality_options)
        self.template_presets.currentIndexChanged.connect(self._apply_template_preset)
        self.template_line.textChanged.connect(self._save_settings)
        self.playlist_checkbox.stateChanged.connect(self._save_settings)
        self.restrict_checkbox.stateChanged.connect(self._save_settings)
        self.quality_combo.currentIndexChanged.connect(self._save_settings)
        self.dir_input.textChanged.connect(self._save_settings)
        self.mp3_btn.toggled.connect(self._save_settings)
        self.mp4_btn.toggled.connect(self._save_settings)

        self.mp3_btn.setChecked(True)
        self._update_quality_options()

        self.setMinimumSize(700, 560)

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
        # Append extracted URLs
        urls = [t for t in (part.strip() for part in text_parts) if t]
        if urls:
            current = self.url_input.toPlainText().strip()
            joined = "\n".join(urls)
            self.url_input.setPlainText((current + "\n" + joined).strip() if current else joined)
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
        self.playlist_checkbox.setChecked(bool(playlist))
        self.restrict_checkbox.setChecked(bool(restrict))

        preset_index = self.settings.value("template_preset_index", 0, type=int)
        if 0 <= preset_index < self.template_presets.count():
            self.template_presets.setCurrentIndex(preset_index)
        template = self.settings.value("outtmpl_template", "%(title).150s", type=str)
        self.template_line.setText(template)

    def _save_settings(self) -> None:
        self.settings.setValue("directory", self.dir_input.text().strip())
        is_mp3 = self.mp3_btn.isChecked()
        self.settings.setValue("is_mp3", is_mp3)
        self.settings.setValue("quality", self.quality_combo.currentText())
        self.settings.setValue("download_playlist", self.playlist_checkbox.isChecked())
        self.settings.setValue("restrict_filenames", self.restrict_checkbox.isChecked())
        self.settings.setValue("template_preset_index", self.template_presets.currentIndex())
        self.settings.setValue("outtmpl_template", self.template_line.text())

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
        self.playlist_checkbox.setEnabled(enabled)
        self.restrict_checkbox.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)

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
            return f"Cannot create directory:\n{directory}\n{e}"
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

        opts = DownloadOptions(
            is_mp3=self.mp3_btn.isChecked(),
            quality=self.quality_combo.currentText(),
            outtmpl_template=self.template_line.text(),
            directory=self.dir_input.text().strip(),
            download_playlist=self.playlist_checkbox.isChecked(),
            restrict_filenames=self.restrict_checkbox.isChecked(),
        )

        self._worker_thread = QThread(self)
        self._worker = VideoDownloadWorker(urls, opts)
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

        self._set_controls_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")
        self.append_log(f"Queue size: {len(urls)}")
        self.append_log(f"Format: {'MP3' if opts.is_mp3 else 'MP4'} | Quality: {opts.quality}")
        self.append_log(f"Output dir: {opts.directory}")
        self.append_log(f"Template: {opts.outtmpl_template}.%(ext)s")
        self.append_log(f"Playlist: {'Yes' if opts.download_playlist else 'No'} | Restrict filenames: {'Yes' if opts.restrict_filenames else 'No'}")
        if not self._ffmpeg_available:
            self.append_log("Warning: ffmpeg not found on PATH. Audio extraction and metadata embedding may fail.")
        self._worker_thread.start()

    def _cancel_downloads(self) -> None:
        if self._worker:
            self.append_log("Cancellation requested...")
            self.status_label.setText("Cancelling...")
            self.cancel_button.setEnabled(False)
            self._worker.cancel()

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
            self.append_log(f"SUCCESS: {url}\nSaved to: {info}")
        else:
            self.append_log(f"FAILED: {url}\nReason: {info}")

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
            if self._worker:
                self._worker.cancel()
            if self._worker_thread and self._worker_thread.isRunning():
                self._worker_thread.quit()
                self._worker_thread.wait(5000)
        except Exception:
            pass
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = MainWindow()
    if not win.dir_input.text().strip():
        win.dir_input.setText(win._default_download_dir())
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
