import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def _application_search_dirs() -> List[Path]:
    """Return trusted app-owned directories for bundled tools."""
    dirs: List[Path] = []

    if getattr(sys, "frozen", False):
        # PyInstaller extracts bundled binaries into _MEIPASS. Users may also
        # place tools beside the executable for standard/non-standalone builds.
        dirs.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)))
        dirs.append(Path(sys.executable).resolve().parent)
    else:
        # Source checkout root: core/utils.py -> project root.
        dirs.append(Path(__file__).resolve().parents[1])

    unique: List[Path] = []
    seen: set[str] = set()
    for directory in dirs:
        try:
            resolved = directory.resolve()
        except Exception:
            resolved = directory
        key = os.path.normcase(str(resolved))
        if key not in seen:
            unique.append(resolved)
            seen.add(key)
    return unique


def get_tool_path(executable_name: str, extra_dirs: Optional[Iterable[os.PathLike | str]] = None) -> Optional[str]:
    """
    Locate an external tool with safe precedence.

    Resolution order:
    1. Explicit extra directories supplied by the caller/test.
    2. Trusted app-owned directories: PyInstaller bundle, executable dir, or
       source checkout root.
    3. System PATH.

    This intentionally does not search arbitrary current working directories;
    doing so can execute the wrong binary when the app is launched elsewhere.
    """
    if not executable_name:
        return None

    search_dirs: List[Path] = []
    if extra_dirs:
        search_dirs.extend(Path(directory) for directory in extra_dirs)
    search_dirs.extend(_application_search_dirs())

    seen: set[str] = set()
    for directory in search_dirs:
        candidate = directory / executable_name
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists() and resolved.is_file():
            return str(resolved)

    return shutil.which(executable_name)


def get_ffmpeg_path() -> Optional[str]:
    """Locate ffmpeg.exe in the bundle/app directory or system PATH."""
    return get_tool_path("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")


def get_aria2c_path() -> Optional[str]:
    """Locate aria2c.exe in the bundle/app directory or system PATH."""
    return get_tool_path("aria2c.exe" if sys.platform == "win32" else "aria2c")


def get_tool_version(executable_path: Optional[str], *args: str, timeout: float = 3.0) -> str:
    """Return the first version line for a tool, or 'unknown'."""
    if not executable_path:
        return "unknown"
    try:
        result = subprocess.run(
            [executable_path, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except Exception:
        return "unknown"

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    for line in output.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return "unknown"


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
