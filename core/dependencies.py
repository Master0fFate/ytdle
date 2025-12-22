import shutil
import sys
import yt_dlp
from typing import Dict
from core.utils import get_ffmpeg_path

def check_dependencies() -> Dict[str, str]:
    """
    Checks availability of FFmpeg and yt-dlp version.
    """
    ffmpeg_path = get_ffmpeg_path()
    
    deps = {
        "ffmpeg": ffmpeg_path if ffmpeg_path else "Not found",
        "yt_dlp": yt_dlp.version.__version__
    }
    return deps
