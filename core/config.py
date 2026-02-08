from dataclasses import dataclass, field
from typing import Optional, Tuple

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
    cookies: str = None
    ffmpeg_args: str = None
    ffmpeg_add_args: str = None
    ffmpeg_override_args: str = None
    # Browser cookie fetching: (browser_name, profile, keyring, container)
    # e.g., ("chrome", None, None, None) or ("firefox", "default", None, "Personal")
    cookies_from_browser: Optional[Tuple[str, Optional[str], Optional[str], Optional[str]]] = None
    # Aria2c high-performance download options
    use_aria2c: bool = False
    max_connections: int = 16
    # Async download options
    max_concurrent_downloads: int = 3