"""Terminal interface for YTDLE.

This module keeps terminal downloads on the same options, cookie policy, history,
and saved QSettings values as the desktop application.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import socket
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

from PySide6.QtCore import QSettings

from core.config import DownloadOptions
from core.dependencies import check_dependencies
from core.history import DownloadHistory
from core.logger import setup_logging
from core.utils import get_aria2c_path

APP_ORGANIZATION = "Merlin"
APP_NAME = "YTDLE_v2"
COOKIE_FILE_SOURCE = "Cookie File (Fallback)"
SUPPORTED_BROWSERS = frozenset(
    {
        "brave",
        "chrome",
        "chromium",
        "edge",
        "firefox",
        "opera",
        "safari",
        "vivaldi",
    }
)
MP3_QUALITIES = ("320k", "256k", "192k", "128k")
MP4_QUALITIES = ("Best", "2160p", "1440p", "1080p", "720p", "480p", "360p")
MAX_URL_LIST_BYTES = 5 * 1024 * 1024
MAX_CONNECTIONS = 32
MAX_RETRIES = 100


class CliValidationError(ValueError):
    """Raised when a CLI value is syntactically valid but unusable."""


@dataclass(frozen=True)
class SavedDownloadSettings:
    directory: str
    is_mp3: bool
    quality: str
    download_playlist: bool
    restrict_filenames: bool
    use_async: bool
    use_aria2c: bool
    output_template: str
    ffmpeg_args: str
    ffmpeg_mode: str
    cookie_source: str
    cookie_file: str
    browser_profile: str
    browser_keyring: str
    browser_container: str


@dataclass(frozen=True)
class ResolvedDownloadConfig:
    options: DownloadOptions
    use_async: bool
    max_concurrent_downloads: int
    verbose: bool
    cookie_source: str
    cookie_file: str | None
    browser: str | None
    browser_profile: str | None
    browser_keyring: str | None
    browser_container: str | None
    ffmpeg_mode: str


@dataclass(frozen=True)
class UrlInput:
    value: str
    source: str


def _settings_value(
    settings: QSettings, key: str, default: Any, value_type: type[Any]
) -> Any:
    """Read a QSettings value while keeping tests independent of Qt's overload."""
    try:
        return settings.value(key, default, type=value_type)
    except TypeError:
        return settings.value(key, default)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _default_download_directory() -> str:
    return str(Path.home() / "YTDLE")


def _normalise_saved_cookie_source(value: str) -> str:
    source = (value or "None").strip()
    lowered = source.lower()
    if lowered == "none":
        return "none"
    if lowered == COOKIE_FILE_SOURCE.lower():
        return "file"
    if lowered in SUPPORTED_BROWSERS:
        return lowered
    return "none"


def load_saved_download_settings(
    settings: QSettings | None = None,
) -> SavedDownloadSettings:
    """Load the same persisted selections that the desktop window loads."""
    settings = settings or QSettings(APP_ORGANIZATION, APP_NAME)
    cookie_file = str(
        _settings_value(settings, "cookie_file", "", str) or ""
    ).strip()
    cookie_source = _normalise_saved_cookie_source(
        str(_settings_value(settings, "cookie_browser", "None", str) or "None")
    )
    # The GUI keeps compatibility with old configurations that stored a file
    # but did not record its source. The CLI does the same.
    if cookie_source == "none" and cookie_file:
        cookie_source = "file"

    return SavedDownloadSettings(
        directory=str(
            _settings_value(settings, "directory", _default_download_directory(), str)
            or _default_download_directory()
        ).strip(),
        is_mp3=_as_bool(_settings_value(settings, "is_mp3", True, bool)),
        quality=str(_settings_value(settings, "quality", "320k", str) or "320k").strip(),
        download_playlist=_as_bool(
            _settings_value(settings, "download_playlist", False, bool)
        ),
        restrict_filenames=_as_bool(
            _settings_value(settings, "restrict_filenames", False, bool)
        ),
        use_async=_as_bool(_settings_value(settings, "use_async", True, bool)),
        use_aria2c=_as_bool(_settings_value(settings, "use_aria2c", False, bool)),
        output_template=str(
            _settings_value(settings, "outtmpl_template", "%(title).150s", str)
            or "%(title).150s"
        ).strip(),
        ffmpeg_args=str(_settings_value(settings, "ffmpeg_args", "", str) or "").strip(),
        ffmpeg_mode=str(
            _settings_value(settings, "ffmpeg_mode", "Append", str) or "Append"
        ).strip(),
        cookie_source=cookie_source,
        cookie_file=cookie_file,
        browser_profile=str(
            _settings_value(settings, "cookie_profile", "", str) or ""
        ).strip(),
        browser_keyring=str(
            _settings_value(settings, "cookie_keyring", "", str) or ""
        ).strip(),
        browser_container=str(
            _settings_value(settings, "cookie_container", "", str) or ""
        ).strip(),
    )


def _option(args: argparse.Namespace, name: str, fallback: Any) -> Any:
    return getattr(args, name, fallback)


def _normalise_quality(value: str, is_mp3: bool) -> str:
    normalized = (value or "").strip()
    allowed = MP3_QUALITIES if is_mp3 else MP4_QUALITIES
    canonical = {item.lower(): item for item in allowed}
    result = canonical.get(normalized.lower())
    if result:
        return result
    expected = ", ".join(allowed)
    media_type = "MP3 bitrate" if is_mp3 else "MP4 resolution"
    raise CliValidationError(
        f"Invalid {media_type} {value!r}. Use one of: {expected}."
    )


def _normalise_ffmpeg_mode(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"append", "override"}:
        return normalized
    raise CliValidationError(
        f"Invalid --ffmpeg-mode {value!r}. Use 'append' or 'override'."
    )


def _validate_ffmpeg_args(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        shlex.split(value)
    except ValueError as error:
        raise CliValidationError(
            "Invalid FFmpeg arguments: "
            f"{error}. Close every quote or remove the unmatched quote."
        ) from error
    return value


def _int_option(
    args: argparse.Namespace,
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
    flag: str,
) -> int:
    value = _option(args, name, default)
    if value < minimum or value > maximum:
        raise CliValidationError(
            f"{flag} must be an integer from {minimum} to {maximum}; got {value}."
        )
    return value


def _cookie_source_from_args(
    args: argparse.Namespace, saved: SavedDownloadSettings
) -> tuple[str, str | None, str | None]:
    """Return source kind, browser name, and cookie-file path."""
    if getattr(args, "no_cookies", False):
        return "none", None, None
    if hasattr(args, "cookies_from_browser"):
        browser = args.cookies_from_browser.strip().lower()
        if browser not in SUPPORTED_BROWSERS:
            expected = ", ".join(sorted(SUPPORTED_BROWSERS))
            raise CliValidationError(
                f"Invalid --cookies-from-browser {browser!r}. Use one of: {expected}."
            )
        return browser, browser, None
    if hasattr(args, "cookies_file"):
        cookie_file = args.cookies_file.strip()
        if not cookie_file:
            raise CliValidationError("--cookies-file needs a non-empty file path.")
        return "file", None, cookie_file
    if saved.cookie_source == "file":
        return "file", None, saved.cookie_file
    if saved.cookie_source in SUPPORTED_BROWSERS:
        return saved.cookie_source, saved.cookie_source, None
    return "none", None, None


def resolve_download_config(
    args: argparse.Namespace,
    saved: SavedDownloadSettings | None = None,
    *,
    validate_saved_cookie_file: bool = True,
) -> ResolvedDownloadConfig:
    """Resolve CLI overrides over saved GUI selections and validate all values."""
    saved = saved or load_saved_download_settings()
    media_format = _option(args, "media_format", "mp3" if saved.is_mp3 else "mp4")
    is_mp3 = media_format == "mp3"

    saved_quality = saved.quality or ("320k" if saved.is_mp3 else "Best")
    requested_quality = _option(args, "quality", saved_quality)
    try:
        quality = _normalise_quality(requested_quality, is_mp3)
    except CliValidationError:
        # Changing media type in the GUI resets the quality list. Do the same
        # when the caller explicitly changes only --format.
        if hasattr(args, "media_format") and not hasattr(args, "quality"):
            quality = "320k" if is_mp3 else "Best"
        else:
            raise

    directory = str(_option(args, "output_dir", saved.directory)).strip()
    if not directory:
        raise CliValidationError(
            "--output-dir is empty. Give a directory path, for example --output-dir C:\\Downloads."
        )
    directory = os.path.abspath(os.path.expanduser(directory))

    output_template = str(
        _option(args, "output_template", saved.output_template)
    ).strip()
    if not output_template:
        raise CliValidationError(
            "--output-template is empty. Use a yt-dlp pattern such as '%(title).150s'."
        )

    ffmpeg_args = _option(args, "ffmpeg_args", saved.ffmpeg_args)
    ffmpeg_mode = _option(args, "ffmpeg_mode", saved.ffmpeg_mode)
    if hasattr(args, "legacy_ffmpeg_add_args"):
        ffmpeg_args = args.legacy_ffmpeg_add_args
        if hasattr(args, "ffmpeg_mode") and _normalise_ffmpeg_mode(ffmpeg_mode) != "append":
            raise CliValidationError(
                "--ffmpeg-add-args can only be used with --ffmpeg-mode append."
            )
        ffmpeg_mode = "append"
    if hasattr(args, "legacy_ffmpeg_override_args"):
        ffmpeg_args = args.legacy_ffmpeg_override_args
        if hasattr(args, "ffmpeg_mode") and _normalise_ffmpeg_mode(ffmpeg_mode) != "override":
            raise CliValidationError(
                "--ffmpeg-override-args can only be used with --ffmpeg-mode override."
            )
        ffmpeg_mode = "override"
    ffmpeg_args = _validate_ffmpeg_args(str(ffmpeg_args or ""))
    ffmpeg_mode = _normalise_ffmpeg_mode(str(ffmpeg_mode or "Append"))

    cookie_source, browser, cookie_file = _cookie_source_from_args(args, saved)
    profile = str(_option(args, "browser_profile", saved.browser_profile) or "").strip()
    keyring = str(_option(args, "browser_keyring", saved.browser_keyring) or "").strip()
    container = str(_option(args, "browser_container", saved.browser_container) or "").strip()
    browser_fields_given = any(
        hasattr(args, name)
        for name in ("browser_profile", "browser_keyring", "browser_container")
    )
    if browser_fields_given and browser is None:
        raise CliValidationError(
            "--browser-profile, --browser-keyring, and --browser-container need "
            "--cookies-from-browser BROWSER."
        )

    cookies_from_browser = None
    if browser:
        cookies_from_browser = (
            browser,
            profile or None,
            keyring or None,
            container or None,
        )
    elif cookie_source == "file":
        if not cookie_file:
            raise CliValidationError(
                "Cookie-file mode is selected but no cookie file is set. Use "
                "--cookies-file PATH or --no-cookies."
            )
        cookie_file = os.path.abspath(os.path.expanduser(cookie_file))
        if not os.path.isfile(cookie_file) and (
            validate_saved_cookie_file or hasattr(args, "cookies_file")
        ):
            raise CliValidationError(
                f"Cookie file was not found: {cookie_file}. Choose an existing Netscape cookies.txt file."
            )

    use_aria2c = bool(_option(args, "use_aria2c", saved.use_aria2c))
    if use_aria2c and not get_aria2c_path():
        raise CliValidationError(
            "aria2c is enabled but was not found. Put aria2c beside YTDLE, add it "
            "to PATH, or pass --no-aria2c."
        )

    options = DownloadOptions(
        is_mp3=is_mp3,
        quality=quality,
        outtmpl_template=output_template,
        directory=directory,
        download_playlist=bool(
            _option(args, "download_playlist", saved.download_playlist)
        ),
        restrict_filenames=bool(
            _option(args, "restrict_filenames", saved.restrict_filenames)
        ),
        retries=_int_option(
            args,
            "retries",
            10,
            minimum=0,
            maximum=MAX_RETRIES,
            flag="--retries",
        ),
        fragment_retries=_int_option(
            args,
            "fragment_retries",
            10,
            minimum=0,
            maximum=MAX_RETRIES,
            flag="--fragment-retries",
        ),
        concurrent_fragment_downloads=_int_option(
            args,
            "fragment_concurrency",
            3,
            minimum=1,
            maximum=MAX_CONNECTIONS,
            flag="--fragment-concurrency",
        ),
        nocheckcertificate=bool(getattr(args, "no_check_certificate", False)),
        cookies=cookie_file,
        ffmpeg_add_args=ffmpeg_args if ffmpeg_mode == "append" and ffmpeg_args else None,
        ffmpeg_override_args=(
            ffmpeg_args if ffmpeg_mode == "override" and ffmpeg_args else None
        ),
        cookies_from_browser=cookies_from_browser,
        use_aria2c=use_aria2c,
        max_connections=_int_option(
            args,
            "connections",
            16,
            minimum=1,
            maximum=MAX_CONNECTIONS,
            flag="--connections",
        ),
        max_concurrent_downloads=_int_option(
            args,
            "concurrent_downloads",
            3,
            minimum=1,
            maximum=MAX_CONNECTIONS,
            flag="--concurrent-downloads",
        ),
    )
    return ResolvedDownloadConfig(
        options=options,
        use_async=bool(_option(args, "use_async", saved.use_async)),
        max_concurrent_downloads=options.max_concurrent_downloads,
        verbose=bool(getattr(args, "verbose", False)),
        cookie_source=cookie_source,
        cookie_file=cookie_file,
        browser=browser,
        browser_profile=profile or None,
        browser_keyring=keyring or None,
        browser_container=container or None,
        ffmpeg_mode=ffmpeg_mode,
    )


def _read_url_input_file(path_value: str) -> list[UrlInput]:
    """Read one UTF-8 line list without hiding read or encoding failures."""
    if not path_value.strip():
        raise CliValidationError("--input-file needs a file path or '-'.")
    if path_value == "-":
        contents = sys.stdin.read()
        source_name = "standard input"
        if len(contents.encode("utf-8")) > MAX_URL_LIST_BYTES:
            raise CliValidationError(
                "Standard input is larger than 5 MiB. Split the URL list into smaller batches."
            )
    else:
        path = Path(path_value).expanduser()
        if not path.is_file():
            raise CliValidationError(
                f"Input file was not found: {path}. Use a UTF-8 text file, or pass --url URL."
            )
        try:
            if path.stat().st_size > MAX_URL_LIST_BYTES:
                raise CliValidationError(
                    f"Input file is larger than 5 MiB: {path}. Split it into smaller batches."
                )
            contents = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as error:
            raise CliValidationError(
                f"Cannot read {path} as UTF-8 text: {error}. Save it as UTF-8 and retry."
            ) from error
        except OSError as error:
            raise CliValidationError(
                f"Cannot read input file {path}: {error}. Check the file and permissions."
            ) from error
        source_name = str(path)
    return [
        UrlInput(value=line.strip(), source=f"{source_name}:{number}")
        for number, line in enumerate(contents.splitlines(), start=1)
    ]


def _url_error(value: str) -> str | None:
    if len(value.split()) != 1:
        return "contains spaces"
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return "is malformed"
    if parsed.scheme.lower() not in {"http", "https"}:
        return "must start with http:// or https://"
    if not hostname:
        return "is missing a website host"
    return None


def collect_urls(args: argparse.Namespace) -> list[str]:
    """Collect every requested URL, rejecting every invalid item before download."""
    entries: list[UrlInput] = []
    for number, value in enumerate(getattr(args, "urls", ()) or (), start=1):
        entries.append(UrlInput(value=str(value).strip(), source=f"--url #{number}"))
    for input_file in getattr(args, "input_files", ()) or ():
        entries.extend(_read_url_input_file(input_file))

    if not entries:
        raise CliValidationError(
            "No download input was provided. Use --url URL, --input URL [...], or --input-file PATH."
        )

    urls: list[str] = []
    errors: list[str] = []
    ignored_comments = 0
    ignored_blank_lines = 0
    duplicate_count = 0
    seen: set[str] = set()
    for entry in entries:
        if not entry.value:
            if entry.source.startswith("--url"):
                errors.append(f"{entry.source}: is empty")
            else:
                ignored_blank_lines += 1
            continue
        if entry.value.startswith("#"):
            ignored_comments += 1
            continue
        reason = _url_error(entry.value)
        if reason:
            errors.append(f"{entry.source}: {reason} ({entry.value!r})")
            continue
        if entry.value in seen:
            duplicate_count += 1
        seen.add(entry.value)
        urls.append(entry.value)

    if errors:
        joined = "\n  - ".join(errors)
        raise CliValidationError(
            "Invalid download input. Replace every item below with a full HTTP(S) URL:\n"
            f"  - {joined}"
        )
    if not urls:
        raise CliValidationError(
            "No URLs were found. Input files may contain blank lines and # comments, "
            "but they need at least one HTTP(S) URL."
        )
    if ignored_comments or ignored_blank_lines:
        print(
            "Input note: ignored "
            f"{ignored_blank_lines} blank line(s) and {ignored_comments} comment line(s)."
        )
    if duplicate_count:
        print(
            f"Input note: {duplicate_count} duplicate URL occurrence(s) will be downloaded as requested."
        )
    return urls


def _prepare_output_directory(config: ResolvedDownloadConfig) -> None:
    directory = config.options.directory
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as error:
        raise CliValidationError(
            f"Cannot create output directory {directory}: {error}. Check the path and permissions."
        ) from error
    if not os.path.isdir(directory):
        raise CliValidationError(
            f"Output path is not a directory: {directory}. Pass --output-dir DIRECTORY."
        )


def _open_history(path_value: str | None) -> DownloadHistory:
    if path_value is None:
        return DownloadHistory()
    if not path_value.strip():
        raise CliValidationError("--history-file needs a non-empty file path.")
    path = Path(path_value).expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return DownloadHistory(str(path))
    except (OSError, RuntimeError) as error:
        raise CliValidationError(
            f"Cannot open history at {path}: {error}. Check the path and permissions."
        ) from error


def _print_download_configuration(config: ResolvedDownloadConfig, url_count: int) -> None:
    options = config.options
    cookie_description = "none"
    if config.browser:
        cookie_description = f"browser {config.browser}"
    elif config.cookie_file:
        cookie_description = f"file {config.cookie_file}"
    print("YTDLE terminal download")
    print(f"Items: {url_count}")
    print(f"Output directory: {options.directory}")
    print(
        f"Format: {'MP3' if options.is_mp3 else 'MP4'} | Quality: {options.quality}"
    )
    print(
        f"Playlist: {options.download_playlist} | Restrict filenames: {options.restrict_filenames}"
    )
    print(
        f"Engine: {'async' if config.use_async else 'sequential'} | "
        f"Concurrent downloads: {config.max_concurrent_downloads}"
    )
    print(f"Cookies: {cookie_description}")
    print("-" * 40)


def run_download(
    urls: Sequence[str],
    config: ResolvedDownloadConfig,
    history_file: str | None,
) -> int:
    """Download a complete validated batch and return a process exit code."""
    _prepare_output_directory(config)
    setup_logging(verbose=config.verbose)
    history = _open_history(history_file)
    manager: Any | None = None
    output_lock = threading.Lock()
    result = {"success": 0, "failed": 0}

    def emit(message: str, *, stream: Any = sys.stdout) -> None:
        with output_lock:
            print(message, file=stream, flush=True)

    def on_progress(pct: int) -> None:
        if config.verbose:
            emit(f"Progress: {pct}%")

    def on_status(message: str) -> None:
        if config.verbose:
            emit(f"Status: {message}")

    def on_log(message: str) -> None:
        if config.verbose:
            emit(f"Log: {message}")

    def on_error(message: str) -> None:
        emit(f"ERROR: {message}", stream=sys.stderr)

    def on_item_started(url: str) -> None:
        emit(f"START: {url}")

    def on_item_finished(url: str, success: bool, info: str) -> None:
        state = "SUCCESS" if success else "FAILED"
        stream = sys.stdout if success else sys.stderr
        emit(f"{state}: {url}\n  {info}", stream=stream)

    def on_all_finished(success: int, failed: int) -> None:
        result["success"] = success
        result["failed"] = failed

    _print_download_configuration(config, len(urls))
    try:
        if config.use_async:
            from core.async_manager import AsyncDownloadManager

            manager = AsyncDownloadManager(
                list(urls),
                config.options,
                on_progress=on_progress,
                on_status=on_status,
                on_log=on_log,
                on_error=on_error,
                on_item_started=on_item_started,
                on_item_finished=on_item_finished,
                on_all_finished=on_all_finished,
                history=history,
                max_concurrent=config.max_concurrent_downloads,
            )
        else:
            from core.downloader import DownloadManager

            manager = DownloadManager(
                list(urls),
                config.options,
                on_progress=on_progress,
                on_status=on_status,
                on_log=on_log,
                on_error=on_error,
                on_item_started=on_item_started,
                on_item_finished=on_item_finished,
                on_all_finished=on_all_finished,
                history=history,
            )
        manager.run()
    except KeyboardInterrupt:
        if manager is not None:
            manager.cancel()
        emit("Cancelled by user.", stream=sys.stderr)
        return 1
    except Exception as error:
        emit(f"ERROR: Unable to run the download batch: {error}", stream=sys.stderr)
        return 1
    finally:
        history.close()

    emit(
        f"Batch complete. Success: {result['success']}, Failed: {result['failed']}."
    )
    return 1 if result["failed"] else 0


def _record_matches(record: Any, query: str) -> bool:
    values = (
        record.url,
        record.title,
        record.format,
        record.quality,
        record.output_path,
        record.error_message,
    )
    query = query.casefold()
    return any(query in (value or "").casefold() for value in values)


def _record_json(record: Any) -> dict[str, Any]:
    return {
        "url": record.url,
        "title": record.title,
        "format": record.format,
        "quality": record.quality,
        "timestamp": record.timestamp,
        "output_path": record.output_path,
        "success": record.success,
        "error_message": record.error_message,
        "retry_count": record.retry_count,
    }


def _safe_cell(value: Any) -> str:
    return str(value or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")


def run_history(args: argparse.Namespace) -> int:
    if getattr(args, "yes", False) and not hasattr(args, "clear"):
        raise CliValidationError("--yes is only valid together with --clear.")
    if hasattr(args, "clear") and not getattr(args, "yes", False):
        raise CliValidationError(
            "--clear changes download history. Repeat the command with --yes to confirm."
        )
    if hasattr(args, "clear") and hasattr(args, "export_failed"):
        raise CliValidationError("Use either --clear or --export-failed, not both.")

    history = _open_history(getattr(args, "history_file", None))
    try:
        if hasattr(args, "clear"):
            clear_target = args.clear
            if clear_target == "completed":
                history.clear_completed()
            elif clear_target == "failed":
                history.clear_failed()
            else:
                history.clear_history()
            print(f"Cleared {clear_target} history records.")
            return 0

        if hasattr(args, "export_failed"):
            raw_output_path = args.export_failed.strip()
            if not raw_output_path:
                raise CliValidationError("--export-failed needs an output file path.")
            output_path = Path(raw_output_path).expanduser()
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                raise CliValidationError(
                    f"Cannot create export directory {output_path.parent}: {error}."
                ) from error
            if not history.export_failed(str(output_path)):
                print(
                    f"ERROR: Could not export failed URLs to {output_path}. Check the path and permissions.",
                    file=sys.stderr,
                )
                return 1
            print(f"Exported failed URLs to: {output_path}")
            return 0

        status = args.status
        records = history.get_all()
        if status == "completed":
            records = [record for record in records if record.success]
        elif status == "failed":
            records = [record for record in records if not record.success]
        if hasattr(args, "search"):
            query = args.search.strip()
            if not query:
                raise CliValidationError("--search needs non-empty text.")
            records = [record for record in records if _record_matches(record, query)]
        if hasattr(args, "limit"):
            if args.limit < 1:
                raise CliValidationError("--limit must be an integer of at least 1.")
            records = records[: args.limit]

        if args.output == "json":
            print(json.dumps([_record_json(record) for record in records], indent=2))
            return 0

        if not records:
            print("No matching history records.")
            return 0
        print("STATUS\tTIMESTAMP\tFORMAT\tQUALITY\tTITLE\tURL\tOUTPUT OR ERROR")
        for record in records:
            state = "completed" if record.success else "failed"
            last_value = record.output_path if record.success else record.error_message
            print(
                "\t".join(
                    _safe_cell(value)
                    for value in (
                        state,
                        record.timestamp,
                        record.format,
                        record.quality,
                        record.title,
                        record.url,
                        last_value,
                    )
                )
            )
        return 0
    finally:
        history.close()


def run_retry_failed(args: argparse.Namespace) -> int:
    history = _open_history(getattr(args, "history_file", None))
    try:
        urls = [record.url for record in history.get_failed()]
    finally:
        history.close()
    if not urls:
        raise CliValidationError(
            "There are no failed history records to retry. Run 'YTDLE history --status failed' to inspect history."
        )
    config = resolve_download_config(args)
    print(f"Retrying {len(urls)} failed history record(s).")
    return run_download(urls, config, getattr(args, "history_file", None))


def run_network_check(args: argparse.Namespace) -> int:
    host = args.host.strip()
    if not host:
        raise CliValidationError("--host needs a host name or IP address.")
    if args.port < 1 or args.port > 65535:
        raise CliValidationError("--port must be an integer from 1 to 65535.")
    if args.timeout <= 0 or args.timeout > 60:
        raise CliValidationError("--timeout must be greater than 0 and no more than 60 seconds.")
    try:
        with socket.create_connection((host, args.port), timeout=args.timeout):
            pass
    except OSError as error:
        print(
            f"Offline: cannot connect to {host}:{args.port} within {args.timeout:g}s ({error}).",
            file=sys.stderr,
        )
        return 1
    print(f"Online: connected to {host}:{args.port}.")
    return 0


def run_tools(args: argparse.Namespace) -> int:
    dependencies = check_dependencies()
    if args.output == "json":
        print(json.dumps(dependencies, indent=2))
    else:
        print(f"yt-dlp: {dependencies['yt_dlp']}")
        print(f"ffmpeg: {dependencies['ffmpeg']}")
        print(f"ffmpeg version: {dependencies['ffmpeg_version']}")
        print(f"aria2c: {dependencies['aria2c']}")
        print(f"aria2c version: {dependencies['aria2c_version']}")
    return 0


def _settings_as_dict(config: ResolvedDownloadConfig) -> dict[str, Any]:
    options = config.options
    return {
        "output_dir": options.directory,
        "format": "mp3" if options.is_mp3 else "mp4",
        "quality": options.quality,
        "playlist": options.download_playlist,
        "restrict_filenames": options.restrict_filenames,
        "async": config.use_async,
        "aria2c": options.use_aria2c,
        "output_template": options.outtmpl_template,
        "ffmpeg_args": options.ffmpeg_add_args or options.ffmpeg_override_args or "",
        "ffmpeg_mode": config.ffmpeg_mode,
        "cookie_source": config.cookie_source,
        "cookie_file": config.cookie_file or "",
        "browser_profile": config.browser_profile or "",
        "browser_keyring": config.browser_keyring or "",
        "browser_container": config.browser_container or "",
    }


def _settings_changed(args: argparse.Namespace) -> bool:
    fields = (
        "output_dir",
        "media_format",
        "quality",
        "download_playlist",
        "restrict_filenames",
        "use_async",
        "use_aria2c",
        "output_template",
        "ffmpeg_args",
        "ffmpeg_mode",
        "legacy_ffmpeg_add_args",
        "legacy_ffmpeg_override_args",
        "cookies_file",
        "cookies_from_browser",
        "no_cookies",
        "browser_profile",
        "browser_keyring",
        "browser_container",
    )
    return any(hasattr(args, field) for field in fields)


def save_download_settings(
    config: ResolvedDownloadConfig, settings: QSettings | None = None
) -> None:
    """Persist values with the exact keys and display values used by the GUI."""
    settings = settings or QSettings(APP_ORGANIZATION, APP_NAME)
    options = config.options
    settings.setValue("directory", options.directory)
    settings.setValue("is_mp3", options.is_mp3)
    settings.setValue("quality", options.quality)
    settings.setValue("download_playlist", options.download_playlist)
    settings.setValue("restrict_filenames", options.restrict_filenames)
    settings.setValue("use_async", config.use_async)
    settings.setValue("use_aria2c", options.use_aria2c)
    settings.setValue("outtmpl_template", options.outtmpl_template)
    settings.setValue(
        "ffmpeg_args", options.ffmpeg_add_args or options.ffmpeg_override_args or ""
    )
    settings.setValue(
        "ffmpeg_mode", "Append" if config.ffmpeg_mode == "append" else "Override"
    )
    if config.cookie_source == "file":
        browser_value = COOKIE_FILE_SOURCE
    elif config.browser:
        browser_value = config.browser
    else:
        browser_value = "None"
    settings.setValue("cookie_browser", browser_value)
    settings.setValue("cookie_profile", config.browser_profile or "")
    settings.setValue("cookie_keyring", config.browser_keyring or "")
    settings.setValue("cookie_container", config.browser_container or "")
    settings.setValue("cookie_file", config.cookie_file or "")
    settings.sync()


def run_settings(args: argparse.Namespace) -> int:
    settings = QSettings(APP_ORGANIZATION, APP_NAME)
    saved = load_saved_download_settings(settings)
    if _settings_changed(args):
        config = resolve_download_config(
            args, saved, validate_saved_cookie_file=False
        )
        save_download_settings(config, settings)
        print("Saved YTDLE terminal and GUI download settings.")
        saved = load_saved_download_settings(settings)
    config = resolve_download_config(
        argparse.Namespace(), saved, validate_saved_cookie_file=False
    )
    values = _settings_as_dict(config)
    if args.output == "json":
        print(json.dumps(values, indent=2))
    else:
        for key, value in values.items():
            print(f"{key}: {value}")
    return 0


def _add_history_file_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--history-file",
        metavar="PATH",
        default=argparse.SUPPRESS,
        help="SQLite history path (.db) or legacy .json base path; default: the YTDLE history database.",
    )


def _add_cookie_options(parser: argparse.ArgumentParser) -> None:
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--cookies-file",
        "--cookies",
        metavar="PATH",
        dest="cookies_file",
        default=argparse.SUPPRESS,
        help="Use this existing Netscape cookies.txt file instead of the saved cookie source.",
    )
    source_group.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        dest="cookies_from_browser",
        default=argparse.SUPPRESS,
        help="Read cookies from brave, chrome, chromium, edge, firefox, opera, safari, or vivaldi.",
    )
    source_group.add_argument(
        "--no-cookies",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Do not use the saved cookie file or browser-cookie source.",
    )
    parser.add_argument(
        "--browser-profile",
        metavar="NAME",
        default=argparse.SUPPRESS,
        help="Browser profile for --cookies-from-browser; default: saved profile.",
    )
    parser.add_argument(
        "--browser-keyring",
        metavar="NAME",
        default=argparse.SUPPRESS,
        help="Browser keyring backend for --cookies-from-browser; default: saved keyring.",
    )
    parser.add_argument(
        "--browser-container",
        metavar="NAME",
        default=argparse.SUPPRESS,
        help="Firefox container for --cookies-from-browser; default: saved container.",
    )


def _add_download_options(
    parser: argparse.ArgumentParser,
    *,
    include_inputs: bool,
    include_runtime: bool,
) -> None:
    if include_inputs:
        parser.add_argument(
            "--url",
            dest="urls",
            metavar="URL",
            action="append",
            default=argparse.SUPPRESS,
            help="One HTTP(S) media or playlist URL. Repeat --url for a batch.",
        )
        parser.add_argument(
            "--input",
            "-i",
            dest="urls",
            metavar="URL",
            nargs="+",
            action="extend",
            default=argparse.SUPPRESS,
            help="Compatibility form for one or more HTTP(S) URLs.",
        )
        parser.add_argument(
            "--input-file",
            dest="input_files",
            metavar="PATH|-",
            action="append",
            default=argparse.SUPPRESS,
            help="UTF-8 URL list, one URL per line; '-' reads standard input. Repeat for multiple files.",
        )
    parser.add_argument(
        "--output-dir",
        "-od",
        metavar="DIRECTORY",
        default=argparse.SUPPRESS,
        help="Destination directory; default: saved GUI selection (~/YTDLE when unset).",
    )
    parser.add_argument(
        "--format",
        "-f",
        dest="media_format",
        choices=("mp3", "mp4"),
        default=argparse.SUPPRESS,
        help="Output format; default: saved GUI selection.",
    )
    parser.add_argument(
        "--quality",
        "-q",
        metavar="VALUE",
        default=argparse.SUPPRESS,
        help="MP3: 320k, 256k, 192k, or 128k. MP4: Best, 2160p, 1440p, 1080p, 720p, 480p, or 360p; default: saved selection.",
    )
    parser.add_argument(
        "--output-template",
        "--template",
        "-t",
        metavar="TEMPLATE",
        dest="output_template",
        default=argparse.SUPPRESS,
        help="yt-dlp filename template without extension; default: saved selection.",
    )
    parser.add_argument(
        "--playlist",
        "-p",
        action=argparse.BooleanOptionalAction,
        dest="download_playlist",
        default=argparse.SUPPRESS,
        help="Download all entries from playlist URLs; default: saved selection.",
    )
    parser.add_argument(
        "--restrict-filenames",
        "--restrict",
        "-r",
        action=argparse.BooleanOptionalAction,
        dest="restrict_filenames",
        default=argparse.SUPPRESS,
        help="Use ASCII-safe file names; default: saved selection.",
    )
    parser.add_argument(
        "--async",
        action=argparse.BooleanOptionalAction,
        dest="use_async",
        default=argparse.SUPPRESS,
        help="Use the concurrent download engine; default: saved GUI selection.",
    )
    parser.add_argument(
        "--aria2c",
        action=argparse.BooleanOptionalAction,
        dest="use_aria2c",
        default=argparse.SUPPRESS,
        help="Use aria2c as the external downloader; default: saved GUI selection.",
    )
    ffmpeg_group = parser.add_mutually_exclusive_group()
    ffmpeg_group.add_argument(
        "--ffmpeg-args",
        metavar="ARGS",
        dest="ffmpeg_args",
        default=argparse.SUPPRESS,
        help="Quoted FFmpeg arguments. Pair with --ffmpeg-mode; default: saved arguments.",
    )
    ffmpeg_group.add_argument(
        "--ffmpeg-add-args",
        metavar="ARGS",
        dest="legacy_ffmpeg_add_args",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    ffmpeg_group.add_argument(
        "--ffmpeg-override-args",
        metavar="ARGS",
        dest="legacy_ffmpeg_override_args",
        default=argparse.SUPPRESS,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--ffmpeg-mode",
        choices=("append", "override"),
        default=argparse.SUPPRESS,
        help="Apply --ffmpeg-args by appending or overriding; default: saved GUI selection.",
    )
    _add_cookie_options(parser)

    if not include_runtime:
        return
    parser.add_argument(
        "--connections",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="aria2c connections from 1 to 32; default: 16.",
    )
    parser.add_argument(
        "--concurrent-downloads",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="Async download workers from 1 to 32; default: 3.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="yt-dlp retries per item from 0 to 100; default: 10.",
    )
    parser.add_argument(
        "--fragment-retries",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="yt-dlp retries per fragment from 0 to 100; default: 10.",
    )
    parser.add_argument(
        "--fragment-concurrency",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="Concurrent media fragments from 1 to 32; default: 3.",
    )
    parser.add_argument(
        "--no-check-certificate",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Disable TLS certificate checking for this run; default: certificate checking is enabled.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Print detailed engine status and log messages.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="YTDLE",
        description="YTDLE terminal interface. Run 'YTDLE COMMAND --help' for command flags.",
    )
    commands = parser.add_subparsers(dest="command", title="commands")

    history_parent = argparse.ArgumentParser(add_help=False)
    _add_history_file_option(history_parent)

    download = commands.add_parser(
        "download",
        parents=(history_parent,),
        help="Batch-download HTTP(S) media or playlists.",
        description="Batch-download URLs. Settings flags override saved desktop selections for this run.",
    )
    _add_download_options(download, include_inputs=True, include_runtime=True)

    retry = commands.add_parser(
        "retry-failed",
        parents=(history_parent,),
        help="Retry every failed history record with optional download-setting overrides.",
        description="Retry each failed history record. Do not pass --url or --input-file here.",
    )
    _add_download_options(retry, include_inputs=False, include_runtime=True)

    history = commands.add_parser(
        "history",
        parents=(history_parent,),
        help="List, export, or clear download history.",
    )
    history.add_argument(
        "--status",
        choices=("all", "completed", "failed"),
        default="all",
        help="History status filter; default: all.",
    )
    history.add_argument(
        "--search",
        metavar="TEXT",
        default=argparse.SUPPRESS,
        help="Case-insensitive text filter for URL, title, format, quality, path, or error.",
    )
    history.add_argument(
        "--limit",
        type=int,
        metavar="INTEGER",
        default=argparse.SUPPRESS,
        help="Maximum listed records; default: no limit.",
    )
    history.add_argument(
        "--output",
        choices=("table", "json"),
        default="table",
        help="Listing format; default: table.",
    )
    history.add_argument(
        "--export-failed",
        metavar="PATH",
        default=argparse.SUPPRESS,
        help="Write all failed records as a reusable text URL list.",
    )
    history.add_argument(
        "--clear",
        choices=("completed", "failed", "all"),
        default=argparse.SUPPRESS,
        help="Delete selected history records. Requires --yes.",
    )
    history.add_argument(
        "--yes",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Confirm --clear.",
    )

    network = commands.add_parser(
        "check-network", help="Test the network endpoint used by the desktop app."
    )
    network.add_argument(
        "--host", default="8.8.8.8", help="Host or IP to connect to; default: 8.8.8.8."
    )
    network.add_argument(
        "--port", type=int, default=53, help="TCP port to connect to; default: 53.")
    network.add_argument(
        "--timeout", type=float, default=5.0, help="Connect timeout in seconds; default: 5.")

    tools = commands.add_parser(
        "tools", help="Show resolved yt-dlp, FFmpeg, and aria2c tool paths and versions."
    )
    tools.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Output format; default: text.",
    )

    settings = commands.add_parser(
        "settings", help="Show or save the GUI-compatible download selections."
    )
    _add_download_options(settings, include_inputs=False, include_runtime=False)
    settings.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Output format; default: text.",
    )

    return parser


def _normalise_command_argv(argv: Sequence[str]) -> list[str]:
    """Keep `YTDLE --url ...` as a convenient download shorthand."""
    values = list(argv)
    commands = {"download", "retry-failed", "history", "check-network", "tools", "settings"}
    if values and values[0] not in commands and values[0] not in {"-h", "--help"}:
        return ["download", *values]
    return values


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Run one terminal command and return a standard process exit code."""
    parser = build_parser()
    args = parser.parse_args(_normalise_command_argv(argv if argv is not None else sys.argv[1:]))
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        if args.command == "download":
            config = resolve_download_config(args)
            urls = collect_urls(args)
            return run_download(urls, config, getattr(args, "history_file", None))
        if args.command == "retry-failed":
            return run_retry_failed(args)
        if args.command == "history":
            return run_history(args)
        if args.command == "check-network":
            return run_network_check(args)
        if args.command == "tools":
            return run_tools(args)
        if args.command == "settings":
            return run_settings(args)
    except CliValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        print("Run 'YTDLE --help' or 'YTDLE COMMAND --help' for valid syntax.", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"ERROR: Terminal operation failed: {error}", file=sys.stderr)
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2
