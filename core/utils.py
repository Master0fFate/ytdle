import os
import shutil
import sys
from typing import List, Optional

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def get_ffmpeg_path() -> Optional[str]:
    """
    Locates ffmpeg.exe.
    Prioritizes bundled version (PyInstaller _MEIPASS), then system PATH.
    """

    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        bundled_path = os.path.join(base_path, "ffmpeg.exe")
        if os.path.exists(bundled_path):
            return bundled_path

    cwd_path = os.path.join(os.getcwd(), "ffmpeg.exe")
    if os.path.exists(cwd_path):
        return cwd_path
        
    return shutil.which("ffmpeg")


def check_ffmpeg_available() -> bool:
    return get_ffmpeg_path() is not None


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