"""Pure helpers for validating and merging the GUI download queue."""

from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import parse_qs, urlsplit


SUPPORTED_URL_SCHEMES = frozenset({"http", "https"})
_YOUTUBE_HOSTS = frozenset(
    {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
)


def queue_key(url: str) -> str:
    """Identity used for de-duplication.

    YouTube shares one video under many links (youtu.be, watch?v=, tracking
    parameters), so those compare by video id. A link that also names a
    playlist keeps it: with "Whole playlist" on it downloads more than the
    video. Everything else compares as typed.
    """
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return url
    video = ""
    if host == "youtu.be":
        video = parts.path.strip("/").split("/")[0]
    elif host in _YOUTUBE_HOSTS:
        if parts.path == "/watch":
            video = parse_qs(parts.query).get("v", [""])[0]
        elif parts.path.startswith(("/shorts/", "/live/")):
            video = parts.path.split("/")[2]
    if not video:
        return url
    playlist = parse_qs(parts.query).get("list", [""])[0]
    return f"youtube:{video}" + (f"|list:{playlist}" if playlist else "")


@dataclass(frozen=True, slots=True)
class InvalidQueueEntry:
    line_number: int
    value: str
    reason: str


@dataclass(frozen=True, slots=True)
class QueueAnalysis:
    urls: tuple[str, ...]
    invalid_entries: tuple[InvalidQueueEntry, ...]
    duplicate_count: int = 0
    comment_count: int = 0

    @property
    def cleaned_text(self) -> str:
        return "\n".join(self.urls)

    @property
    def has_cleanup_items(self) -> bool:
        return bool(self.invalid_entries or self.duplicate_count or self.comment_count)


@dataclass(frozen=True, slots=True)
class QueueMergeResult:
    text: str
    added_urls: tuple[str, ...]
    invalid_entries: tuple[InvalidQueueEntry, ...]
    duplicate_count: int = 0
    comment_count: int = 0

    @property
    def added_count(self) -> int:
        return len(self.added_urls)


def analyze_url_queue(text: str) -> QueueAnalysis:
    """Return unique HTTP(S) URLs and actionable issues for queue text."""
    urls: list[str] = []
    invalid_entries: list[InvalidQueueEntry] = []
    seen: set[str] = set()
    duplicate_count = 0
    comment_count = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        value = raw_line.strip()
        if line_number == 1:
            value = value.lstrip("\ufeff")
        if not value:
            continue
        if value.startswith("#"):
            comment_count += 1
            continue

        reason = _invalid_url_reason(value)
        if reason:
            if value in seen:
                duplicate_count += 1
            else:
                seen.add(value)
                invalid_entries.append(InvalidQueueEntry(line_number, value, reason))
            continue

        key = queue_key(value)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        urls.append(value)

    return QueueAnalysis(
        urls=tuple(urls),
        invalid_entries=tuple(invalid_entries),
        duplicate_count=duplicate_count,
        comment_count=comment_count,
    )


def merge_url_queue(
    existing_text: str,
    incoming_texts: Iterable[str],
    *,
    existing_analysis: Optional[QueueAnalysis] = None,
) -> QueueMergeResult:
    """Append valid, new URLs while preserving the user's existing editor text."""
    incoming = analyze_url_queue("\n".join(incoming_texts))
    if existing_analysis is None:
        existing_analysis = analyze_url_queue(existing_text)
    existing_keys = {queue_key(url) for url in existing_analysis.urls}
    added_urls: list[str] = []
    duplicate_count = incoming.duplicate_count

    for url in incoming.urls:
        key = queue_key(url)
        if key in existing_keys:
            duplicate_count += 1
            continue
        existing_keys.add(key)
        added_urls.append(url)

    if added_urls:
        base_text = existing_text.rstrip()
        additions = "\n".join(added_urls)
        merged_text = f"{base_text}\n{additions}" if base_text else additions
    else:
        merged_text = existing_text

    return QueueMergeResult(
        text=merged_text,
        added_urls=tuple(added_urls),
        invalid_entries=incoming.invalid_entries,
        duplicate_count=duplicate_count,
        comment_count=incoming.comment_count,
    )


def _invalid_url_reason(value: str) -> Optional[str]:
    # ``value`` is non-empty and stripped, so one split field is equivalent
    # to scanning every character with str.isspace(), but runs in C.
    if len(value.split()) != 1:
        return "contains spaces"

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        return "is malformed"

    if parsed.scheme.lower() not in SUPPORTED_URL_SCHEMES:
        return "must start with http:// or https://"
    if not hostname:
        return "is missing a website host"
    return None
