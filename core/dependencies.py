import shutil
import sys
import yt_dlp
from importlib import metadata
from typing import Dict
from core.utils import get_ffmpeg_path


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
    Checks availability of FFmpeg and yt-dlp version.
    """
    ffmpeg_path = get_ffmpeg_path()
    
    deps = {
        "ffmpeg": ffmpeg_path if ffmpeg_path else "Not found",
        "yt_dlp": get_yt_dlp_version()
    }
    return deps
