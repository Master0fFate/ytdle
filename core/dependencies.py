import yt_dlp
from importlib import metadata
from typing import Dict
from core.utils import get_aria2c_path, get_ffmpeg_path, get_tool_version


def get_yt_dlp_version() -> str:
    """Resolve yt-dlp version reliably in source and bundled environments."""
    try:
        return yt_dlp.version.__version__
    except Exception:
        pass

    try:
        return metadata.version("yt-dlp")
    except Exception:
        pass

    return "unknown"

def check_dependencies() -> Dict[str, str]:
    """
    Checks availability of external tools and yt-dlp version.
    """
    ffmpeg_path = get_ffmpeg_path()
    aria2c_path = get_aria2c_path()
    
    deps = {
        "ffmpeg": ffmpeg_path if ffmpeg_path else "Not found",
        "ffmpeg_version": get_tool_version(ffmpeg_path, "-version") if ffmpeg_path else "unknown",
        "aria2c": aria2c_path if aria2c_path else "Not found",
        "aria2c_version": get_tool_version(aria2c_path, "--version") if aria2c_path else "unknown",
        "yt_dlp": get_yt_dlp_version(),
    }
    return deps
