from importlib import metadata
from typing import Dict

from core.utils import get_aria2c_path, get_ffmpeg_path, get_tool_version


def get_yt_dlp_version() -> str:
    """Resolve yt-dlp version without importing its full package when possible."""
    try:
        return metadata.version("yt-dlp")
    except metadata.PackageNotFoundError:
        try:
            from yt_dlp.version import __version__
        except (ImportError, AttributeError):
            return "unknown"
        return __version__


def resolve_dependency_paths() -> Dict[str, str]:
    """Resolve authoritative tool availability without launching subprocesses."""
    ffmpeg_path = get_ffmpeg_path()
    aria2c_path = get_aria2c_path()
    return {
        "ffmpeg": ffmpeg_path if ffmpeg_path else "Not found",
        "ffmpeg_version": "unknown",
        "aria2c": aria2c_path if aria2c_path else "Not found",
        "aria2c_version": "unknown",
        "yt_dlp": get_yt_dlp_version(),
    }


def check_dependencies() -> Dict[str, str]:
    """Check tool availability and synchronously probe all version strings."""
    deps = resolve_dependency_paths()
    ffmpeg_path = deps["ffmpeg"]
    aria2c_path = deps["aria2c"]
    if ffmpeg_path != "Not found":
        deps["ffmpeg_version"] = get_tool_version(ffmpeg_path, "-version")
    if aria2c_path != "Not found":
        deps["aria2c_version"] = get_tool_version(aria2c_path, "--version")
    return deps
