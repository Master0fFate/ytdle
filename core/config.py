from dataclasses import dataclass

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