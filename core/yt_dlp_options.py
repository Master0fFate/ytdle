import logging
import os
import shlex
from collections.abc import Callable
from typing import Any

from core.config import DownloadOptions
from core.utils import get_aria2c_path, get_ffmpeg_path, sanitize_template

logger = logging.getLogger(__name__)


def _parse_ffmpeg_args(opts: DownloadOptions) -> list[str]:
    parsed: list[str] = []
    for value in (opts.ffmpeg_args, opts.ffmpeg_add_args, opts.ffmpeg_override_args):
        if not value:
            continue
        try:
            parsed.extend(shlex.split(value))
        except ValueError as exc:
            logger.warning("Failed to parse ffmpeg arguments %r: %s", value, exc)
    return parsed


def _video_format(quality: str, attempt: int) -> str:
    if attempt >= 2:
        return "best"

    if quality.lower() == "best":
        return "bv*+ba/best" if attempt == 0 else "best[ext=mp4]/best"

    digits = "".join(filter(str.isdigit, quality))
    max_height = int(digits) if digits else 1080
    if attempt == 0:
        return (
            f"bv*[height<={max_height}]+ba/"
            f"b[height<={max_height}]/best[height<={max_height}]/best"
        )
    return f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best"


def build_yt_dlp_options(
    opts: DownloadOptions,
    progress_hook: Callable[[dict[str, Any]], None],
    attempt: int = 0,
) -> dict[str, Any]:
    """Build the shared yt-dlp policy used by both download engines."""
    options: dict[str, Any] = {
        "outtmpl": os.path.join(
            opts.directory,
            f"{sanitize_template(opts.outtmpl_template)}.%(ext)s",
        ),
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

    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        options["ffmpeg_location"] = ffmpeg_path

    if opts.use_aria2c:
        connections = str(opts.max_connections)
        options.update(
            {
                "external_downloader": get_aria2c_path() or "aria2c",
                "external_downloader_args": {
                    "aria2c": [
                        "-x",
                        connections,
                        "-s",
                        connections,
                        "-k",
                        "1M",
                        "--file-allocation=none",
                        "--optimize-concurrent-downloads=true",
                    ]
                },
            }
        )

    if opts.cookies_from_browser:
        options["cookiesfrombrowser"] = opts.cookies_from_browser
    elif opts.cookies:
        options["cookiefile"] = opts.cookies

    ffmpeg_args = _parse_ffmpeg_args(opts)
    if ffmpeg_args:
        options["postprocessor_args"] = {"ffmpeg": ffmpeg_args}

    if opts.is_mp3:
        bitrate = "".join(filter(str.isdigit, opts.quality)) or "192"
        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": bitrate,
                    },
                    {"key": "FFmpegMetadata"},
                    {"key": "EmbedThumbnail"},
                ],
                "writethumbnail": True,
            }
        )
    else:
        options.update(
            {
                "format": _video_format(opts.quality, attempt),
                "merge_output_format": "mp4",
                "postprocessors": [{"key": "FFmpegMetadata"}],
            }
        )

    return options
