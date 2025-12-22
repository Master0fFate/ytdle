import logging
import os
import threading
import traceback
from typing import Callable, Dict, List, Optional, Set

import yt_dlp
from PySide6.QtCore import QObject, Signal

from core.config import DownloadOptions
from core.utils import sanitize_template, format_status, format_eta, get_ffmpeg_path
from core.history import DownloadHistory
from core.errors import classify_error, FormatNotAvailableError, DownloadError
from core.network import NetworkMonitor, NetworkStatus

logger = logging.getLogger(__name__)


def build_yt_dlp_options(opts: DownloadOptions, progress_hook: Callable, attempt: int = 0) -> Dict:
    outtmpl = os.path.join(opts.directory, f"{sanitize_template(opts.outtmpl_template)}.%(ext)s")
    
    ffmpeg_loc = get_ffmpeg_path()

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
    
    if ffmpeg_loc:
        base["ffmpeg_location"] = ffmpeg_loc
        
    if opts.cookies:
        base["cookiefile"] = opts.cookies
        
    custom_ffmpeg_args = []
    
    if opts.ffmpeg_args:
        custom_ffmpeg_args.append(opts.ffmpeg_args)
        
    if opts.ffmpeg_add_args:
        custom_ffmpeg_args.append(opts.ffmpeg_add_args)
    if opts.ffmpeg_override_args:
        custom_ffmpeg_args.append(opts.ffmpeg_override_args)
        
    if custom_ffmpeg_args:
        import shlex
        final_args = []
        for arg_str in custom_ffmpeg_args:
            try:
                final_args.extend(shlex.split(arg_str))
            except Exception as e:
                logger.warning(f"Failed to parse ffmpeg arg '{arg_str}': {e}")
        
        if final_args:
            base["postprocessor_args"] = {"ffmpeg": final_args}

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
        if attempt == 0:
            if opts.quality.lower() == "best":
                fmt = "bv*+ba/best"
            else:
                try:
                    h = int("".join(filter(str.isdigit, opts.quality)))
                except ValueError:
                    h = 1080
                fmt = f"bv*[height<={h}]+ba/b[height<={h}]/best[height<={h}]/best"
        elif attempt == 1:
            if opts.quality.lower() == "best":
                fmt = "best[ext=mp4]/best"
            else:
                try:
                    h = int("".join(filter(str.isdigit, opts.quality)))
                except ValueError:
                    h = 1080
                fmt = f"best[height<={h}][ext=mp4]/best[height<={h}]/best"
        else:
            fmt = "best"
            
        base.update({
            "format": fmt,
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegMetadata"}],
        })

    return base


class DownloadManager:
    """
    Core download logic separated from Qt.
    Accepts callbacks for various events.
    """
    def __init__(
        self,
        urls: List[str],
        options: DownloadOptions,
        on_progress: Optional[Callable[[int], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_item_started: Optional[Callable[[str], None]] = None,
        on_item_finished: Optional[Callable[[str, bool, str], None]] = None,
        on_all_finished: Optional[Callable[[int, int], None]] = None,
        history: Optional[DownloadHistory] = None,
    ):
        self.urls = urls
        self.options = options
        self._cancel_event = threading.Event()
        self._history = history
        
        self.on_progress = on_progress
        self.on_status = on_status
        self.on_log = on_log
        self.on_error = on_error
        self.on_item_started = on_item_started
        self.on_item_finished = on_item_finished
        self.on_all_finished = on_all_finished

        self._current_output_file: Optional[str] = None
        self._last_logged_pct: int = -10
        self._artifact_candidates: Set[str] = set()
        self._last_item_dir: Optional[str] = None
        self._last_item_stem: Optional[str] = None
        self._current_title: Optional[str] = None
        self._current_url: Optional[str] = None
        self._skip_current_event = threading.Event()
        self._pause_event = threading.Event()
        self._network_monitor = NetworkMonitor()
        self._paused = False

    def cancel(self) -> None:
        self._cancel_event.set()

    def skip_current(self) -> None:
        self._skip_current_event.set()

    def pause(self) -> None:
        self._pause_event.set()
        self._paused = True

    def resume(self) -> None:
        self._pause_event.clear()
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def check_network(self) -> bool:
        return self._network_monitor.check()

    def get_network_status(self) -> str:
        return self._network_monitor.get_status()

    def _emit_progress(self, val: int) -> None:
        if self.on_progress:
            self.on_progress(val)

    def _emit_status(self, msg: str) -> None:
        if self.on_status:
            self.on_status(msg)

    def _emit_log(self, msg: str) -> None:
        if self.on_log:
            self.on_log(msg)

    def _progress_hook(self, d: Dict) -> None:
        if self._cancel_event.is_set():
            raise RuntimeError("User cancelled")
        if self._skip_current_event.is_set():
            raise RuntimeError("Skip current")

        while self._pause_event.is_set():
            import time
            time.sleep(0.1)
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
                    self._emit_progress(pct)

                speed = d.get("speed")
                eta = d.get("eta")
                status_msg = format_status(speed, eta)
                if self._paused:
                    status_msg = "Paused"
                self._emit_status(status_msg)

                if total and pct >= self._last_logged_pct + 10:
                    self._last_logged_pct = pct - (pct % 10)
                    self._emit_log(f"Progress: {pct}% | {format_status(speed, eta)}")

                filename = d.get("filename") or d.get("tmpfilename")
                if filename:
                    self._current_output_file = filename
                    try:
                        self._artifact_candidates.add(filename)
                        self._last_item_dir = os.path.dirname(filename) or self.options.directory
                        base = os.path.basename(filename)
                        self._last_item_stem = os.path.splitext(base)[0]
                    except Exception:
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
                    except Exception:
                        pass

            elif status == "finished":
                self._emit_status("Processing downloaded file...")
                self._emit_log("Download finished. Running post-processing...")
                filename = d.get("filename") or self._current_output_file
                if filename:
                    self._current_output_file = filename
                    try:
                        self._artifact_candidates.add(filename)
                        self._last_item_dir = os.path.dirname(filename) or self.options.directory
                        base = os.path.basename(filename)
                        self._last_item_stem = os.path.splitext(base)[0]
                    except Exception:
                        pass
                self._emit_progress(100)
        except Exception as e:
            self._emit_log(f"Progress hook error: {e!r}")

    def _download_with_fallback(self, url: str) -> tuple[bool, str]:
        max_attempts = 3 if not self.options.is_mp3 else 1
        self._current_url = url
        self._current_title = None
        last_error = ""
        
        for attempt in range(max_attempts):
            if self._cancel_event.is_set():
                raise RuntimeError("User cancelled")
                
            try:
                ydl_opts = build_yt_dlp_options(self.options, self._progress_hook, attempt)
                
                if attempt > 0:
                    self._emit_log(f"Retrying with fallback format (attempt {attempt + 1}/{max_attempts})")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        self._current_title = info.get("title") or "Unknown title"
                        uploader = info.get("uploader") or info.get("channel") or "Unknown"
                        dur = info.get("duration")
                        dur_str = format_eta(dur) if dur else "?"
                        self._emit_log(f"Info: {self._current_title} | Uploader: {uploader} | Duration: {dur_str}")
                    except Exception as ie:
                        self._emit_log(f"Info probe failed: {ie}")
                    
                    ydl.download([url])
                    return True, last_error
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}", exc_info=True)
                error_str = str(e)
                last_error = error_str
                classified_error = classify_error(e)
                
                if isinstance(classified_error, FormatNotAvailableError):
                    if attempt < max_attempts - 1:
                        self._emit_log(f"Format not available, trying fallback...")
                        continue
                    else:
                        self._emit_log(f"All format attempts failed for {url}")
                        raise
                elif isinstance(classified_error, DownloadError):
                    self._emit_log(f"Download error: {classified_error.__class__.__name__}: {error_str}")
                    if attempt < max_attempts - 1:
                        continue
                raise
                
        return False, last_error

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
                    f"{stem}.mp4",
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
                        self._emit_log(f"Cleanup: removed {path}")
                except Exception as e:
                    self._emit_log(f"Cleanup: failed to remove {path}: {e}")
            if removed == 0:
                self._emit_log("Cleanup: no artifacts found to remove")
        except Exception as e:
            self._emit_log(f"Cleanup error: {e}")

    def run(self) -> None:
        success_count, fail_count = 0, 0
        n = len(self.urls)

        ydl_ver = "unknown"
        try:
            from yt_dlp.version import __version__ as yv
            ydl_ver = yv
        except Exception:
            pass
        self._emit_log(f"yt-dlp version: {ydl_ver}")

        for idx, url in enumerate(self.urls, start=1):
            if self._cancel_event.is_set():
                self._emit_log("Cancellation requested. Stopping before next item.")
                break

            self._last_logged_pct = -10
            self._current_output_file = None
            self._artifact_candidates = set()
            self._last_item_dir = None
            self._last_item_stem = None
            
            if self.on_item_started:
                self.on_item_started(url)
                
            self._emit_status(f"Starting {idx}/{n}")
            self._emit_progress(0)
            self._emit_log(f"Preparing: {url}")

            try:
                os.makedirs(self.options.directory, exist_ok=True)
                
                success, error_msg = self._download_with_fallback(url)
                
                if success:
                    success_count += 1
                    final_path = self._current_output_file or "Completed"
                    if self._history:
                        self._history.add_completed(
                            url=url,
                            title=self._current_title or "Unknown",
                            format="mp3" if self.options.is_mp3 else "mp4",
                            quality=self.options.quality,
                            output_path=final_path
                        )
                    if self.on_item_finished:
                        self.on_item_finished(url, True, final_path)
                    self._emit_log(f"Finished: {final_path}")
                else:
                    fail_count += 1
                    try:
                        self._cleanup_artifacts_for_current_item()
                    except Exception:
                        pass
                    if self._history:
                        self._history.add_failed(
                            url=url,
                            title=self._current_title or "Unknown",
                            format="mp3" if self.options.is_mp3 else "mp4",
                            quality=self.options.quality,
                            error_message=error_msg or "Download failed"
                        )
                    if self.on_item_finished:
                        self.on_item_finished(url, False, "Download failed after all attempts")
                    self._emit_log(f"Failed after all attempts: {url}")
                    
            except Exception as e:
                if str(e) == "User cancelled":
                    try:
                        self._cleanup_artifacts_for_current_item()
                    except Exception:
                        pass
                    if self._history:
                        self._history.add_failed(
                            url=url,
                            title=self._current_title or "Unknown",
                            format="mp3" if self.options.is_mp3 else "mp4",
                            quality=self.options.quality,
                            error_message="Cancelled by user"
                        )
                    if self.on_item_finished:
                        self.on_item_finished(url, False, "Cancelled")
                    self._emit_log(f"Cancelled: {url}")
                    break
                if str(e) == "Skip current":
                    try:
                        self._cleanup_artifacts_for_current_item()
                    except Exception:
                        pass
                    if self._history:
                        self._history.add_failed(
                            url=url,
                            title=self._current_title or "Unknown",
                            format="mp3" if self.options.is_mp3 else "mp4",
                            quality=self.options.quality,
                            error_message="Skipped by user"
                        )
                    if self.on_item_finished:
                        self.on_item_finished(url, False, "Skipped")
                    self._emit_log(f"Skipped: {url}")
                    self._skip_current_event.clear()
                    continue
                fail_count += 1
                error_msg = str(e)
                try:
                    self._cleanup_artifacts_for_current_item()
                except Exception:
                    pass
                if self._history:
                    self._history.add_failed(
                        url=url,
                        title=self._current_title or "Unknown",
                        format="mp3" if self.options.is_mp3 else "mp4",
                        quality=self.options.quality,
                        error_message=error_msg
                    )
                msg = f"Error downloading {url}: {e}"
                logger.error(msg, exc_info=True)
                if self.on_error:
                    self.on_error(msg)
                if self.on_item_finished:
                    self.on_item_finished(url, False, error_msg)
                self._emit_log(msg)

        if self.on_all_finished:
            self.on_all_finished(success_count, fail_count)


class VideoDownloadWorker(QObject):
    """
    Qt Wrapper around DownloadManager.
    """
    progress = Signal(int)
    status = Signal(str)
    itemStarted = Signal(str)
    itemFinished = Signal(str, bool, str)
    allFinished = Signal(int, int)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, urls: List[str], options: DownloadOptions, history: Optional[DownloadHistory] = None):
        super().__init__()
        self._manager = DownloadManager(
            urls=urls,
            options=options,
            on_progress=self.progress.emit,
            on_status=self.status.emit,
            on_log=self.log.emit,
            on_error=self.error.emit,
            on_item_started=self.itemStarted.emit,
            on_item_finished=self.itemFinished.emit,
            on_all_finished=self.allFinished.emit,
            history=history
        )

    def cancel(self) -> None:
        self._manager.cancel()

    def skip_current(self) -> None:
        self._manager.skip_current()

    def pause(self) -> None:
        self._manager.pause()

    def resume(self) -> None:
        self._manager.resume()

    def is_paused(self) -> bool:
        return self._manager.is_paused()

    def check_network(self) -> bool:
        return self._manager.check_network()

    def get_network_status(self) -> str:
        return self._manager.get_network_status()

    def run(self) -> None:
        self._manager.run()