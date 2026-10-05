"""Dev-only UI fixtures: the data YTDLE meets in real use, not the kind demo data.

Each fixture feeds the window through the same boundaries real data uses:
saved settings, the detected toolchain, the history store, the link editor,
and the download worker's signals. Nothing here is imported by the app.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from core.history import HistoryRecord

STATES = ("demo", "worst", "empty", "one", "huge")
STATE_LABELS = {
    "demo": "Demo data",
    "worst": "Worst case",
    "empty": "Empty",
    "one": "One",
    "huge": "1,284 rows",
}

# A real OneDrive-for-Business path shape: display name, tenant name, nested folders.
_ONEDRIVE = (
    r"C:\Users\Aleksandra.Wiśniewska-Kowalczyk\OneDrive - Northwind Industries Holdings"
    r"\Documents\Media archive\2026\Conference recordings"
)


@dataclass
class Event:
    """One worker signal, replayed in order: started, status, progress, finished."""

    kind: str
    url: str = ""
    ok: bool = True
    info: str = ""
    value: int = 0


@dataclass
class Fixture:
    settings: dict
    tools: dict
    links: str
    events: list[Event]
    history: list[HistoryRecord]
    online: bool = True
    finished: tuple[int, int] | None = None  # allFinished(success, fail) when set
    notes: list[str] = field(default_factory=list)


def _tools(ffmpeg=r"C:\Tools\ffmpeg.exe", aria2c=r"C:\Tools\aria2c.exe", **versions):
    return {
        "ffmpeg": ffmpeg,
        "aria2c": aria2c,
        "yt_dlp": versions.get("yt_dlp", "2026.08.19"),
        "ffmpeg_version": versions.get("ffmpeg_version", "ffmpeg version 2026-10-01-git-0b01ed76aa-full_build-www.gyan.dev Copyright (c) 2000-2026"),
        "aria2c_version": versions.get("aria2c_version", "aria2 version 1.37.0"),
    }


def _record(url, title, *, ok=True, path="", error="", fmt="mp3", quality="320k", when="2026-10-04T18:22:00"):
    return HistoryRecord(
        url=url, title=title, format=fmt, quality=quality, timestamp=when,
        output_path=path, success=ok, error_message=error, retry_count=0,
    )


# ---------------------------------------------------------------- demo

def _demo() -> Fixture:
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://vimeo.com/76979871",
        "https://soundcloud.com/example/track",
    ]
    return Fixture(
        settings={"directory": r"C:\Downloads"},
        tools=_tools(),
        links="\n".join(urls),
        events=[
            Event("started", urls[0]),
            Event("finished", urls[0], True, r"C:\Downloads\Never Gonna Give You Up.mp3"),
            Event("started", urls[1]),
            Event("status", info="Downloading... 4.2 MB/s | ETA 0:12"),
            Event("progress", value=40),
        ],
        history=[
            _record(urls[0], "Never Gonna Give You Up", path=r"C:\Downloads\Never Gonna Give You Up.mp3"),
            _record(urls[1], "The New Vimeo Player", ok=False, error="ERROR: This video is private"),
        ],
    )


# ---------------------------------------------------------------- worst case

_W = [
    # Tracking-laden share link from the YouTube app: the part that differs is the id, mid-string.
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf&index=12&pp=gAQBiAQB&si=Kx7Yp2mZqLw3",
    # Same video as row 1, short form: a duplicate the queue cannot see.
    "https://youtu.be/dQw4w9WgXcQ?si=AbCdEfGh12345678",
    "https://www.tiktok.com/@aleksandra.wisniewska.kowalczyk/video/7412345678901234567?is_from_webapp=1&sender_device=pc",
    "https://soundcloud.com/konstantin-oberhauser-wettstein/benachrichtigungseinstellungen-extended-mix-2026-remaster",
    "https://x.com/jo/status/1840000000000000000/video/1",
    "https://bücher.example/vorträge/2026/ölafur-darri-ólafsson-keynote",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
]

_WORST_LINKS = "\n".join(
    [
        "# from Jo — Q3 offsite playlist",
        *_W,
        _W[0],                                   # exact duplicate
        "www.youtube.com/watch?v=abc123XYZ00",   # pasted without scheme
        "htps://vimeo.com/76979871",             # typo
        "  https://example.com/video-with-leading-and-trailing-spaces   ",
    ]
)

_LONG_TITLE = "王秀英 - 【4K HDR】東京の夜景 Tokyo Night Walk 🌃 (2026) [Official Video] ｜ 夜の散歩 · Shinjuku → Shibuya"
_RTL_TITLE = "نور الهدى عبد الرحمن - تلاوة خاشعة"
_VI_TITLE = "Đặng Thị Ngọc Hân - Hà Nội mùa thu (Live at Nhà hát Lớn)"
_ESCAPE_TITLE = "<b>Live</b> &amp; Unplugged **2026** <script>alert(1)</script>"

_BOT_ERROR = (
    "ERROR: [youtube] dQw4w9WgXcQ: Sign in to confirm you’re not a bot. Use --cookies-from-browser or "
    "--cookies for the authentication. See  https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp  "
    "for how to manually pass cookies. Also see  https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies  "
    "for tips on effectively exporting YouTube cookies"
)
_TRACE_ERROR = (
    "ERROR: unable to download video data: HTTP Error 403: Forbidden\n"
    "Traceback (most recent call last):\n"
    '  File "yt_dlp\\YoutubeDL.py", line 3611, in process_info'
)


def _worst() -> Fixture:
    saved = _ONEDRIVE + "\\" + _LONG_TITLE + ".mp4"
    return Fixture(
        settings={
            "directory": _ONEDRIVE,
            "is_mp3": False,
            "quality": "2160p",
            "download_playlist": True,
            "use_aria2c": True,
            "outtmpl_template": "%(uploader)s/%(upload_date>%Y-%m)s/%(playlist_index|)s%(playlist_index& - |)s%(title).150s [%(id)s]",
            "ffmpeg_args": "-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart -metadata comment=\"Northwind archive\"",
            "ffmpeg_mode": "Override",
            "cookie_browser": "firefox",
            "cookie_profile": "Profile 3 (Aleksandra – Work)",
            "cookie_container": "Northwind Industries Holdings — Legal & Compliance",
            "cookie_file": _ONEDRIVE + r"\cookies\www.youtube.com_cookies (1).txt",
        },
        # aria2c missing while enabled; FFmpeg from a system install with a BtbN-style version.
        tools=_tools(
            ffmpeg=r"C:\Program Files\FFmpeg for Audacity and Other Applications\bin\ffmpeg.exe",
            aria2c="Not found",
            ffmpeg_version="ffmpeg version N-117234-g0b01ed76aa-20261001 Copyright (c) 2000-2026 the FFmpeg developers",
            aria2c_version="unknown",
        ),
        links=_WORST_LINKS,
        events=[
            Event("started", _W[0]),
            Event("finished", _W[0], True, saved),
            Event("started", _W[1]),
            Event("finished", _W[1], False, _BOT_ERROR),
            Event("started", _W[2]),
            Event("finished", _W[2], False, "Skipped"),
            Event("started", _W[3]),
            Event("finished", _W[3], False, _TRACE_ERROR),
            Event("started", _W[4]),
            Event("finished", _W[4], True, "Completed"),           # yt-dlp reported no path
            Event("started", _W[5]),
            Event("status", info="Downloading... 1253.4 MB/s | ETA 12:34:56"),
            Event("progress", value=99),
        ],
        online=False,
        history=[
            _record(_W[0], _LONG_TITLE, path=saved, fmt="mp4", quality="2160p"),
            _record(_W[1], "Unknown", ok=False, error=_BOT_ERROR, fmt="mp4", quality="2160p"),
            _record(_W[3], _RTL_TITLE, path=_ONEDRIVE + "\\" + _RTL_TITLE + ".mp3"),
            _record(_W[5], _VI_TITLE, path=_ONEDRIVE + "\\" + _VI_TITLE + ".mp3", when="2026-09-27 08:30:00"),
            _record(_W[6], _ESCAPE_TITLE, ok=False, error=_TRACE_ERROR, when=""),
            _record(_W[7], "", path="", when="1970-01-01T00:00:00"),
        ],
    )


# ---------------------------------------------------------------- empty / one / huge

def _empty() -> Fixture:
    return Fixture(settings={"directory": ""}, tools=_tools(), links="", events=[], history=[])


def _one() -> Fixture:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    return Fixture(
        settings={"directory": r"C:\Downloads"},
        tools=_tools(),
        links=url,
        events=[Event("started", url), Event("finished", url, True, r"C:\Downloads\Never Gonna Give You Up.mp3")],
        finished=(1, 0),
        history=[_record(url, "Never Gonna Give You Up", path=r"C:\Downloads\Never Gonna Give You Up.mp3")],
    )


def _huge() -> Fixture:
    urls = [f"https://www.youtube.com/watch?v=vid{index:08d}" for index in range(1284)]
    events: list[Event] = []
    for index, url in enumerate(urls[:1200]):
        events.append(Event("started", url))
        if index % 9 == 0:
            events.append(Event("finished", url, False, "ERROR: [youtube] Video unavailable. This video is private"))
        else:
            events.append(Event("finished", url, True, rf"C:\Downloads\Archive\Video {index:04d}.mp3"))
    base = datetime(2026, 10, 4, 12, 0)
    history = [
        _record(
            urls[index % len(urls)],
            f"Lecture {index:05d} — Introduction to Signals and Systems",
            ok=index % 7 != 0,
            path=rf"C:\Downloads\Archive\Lecture {index:05d}.mp3",
            error="ERROR: HTTP Error 429: Too Many Requests",
            when=(base - timedelta(minutes=index)).isoformat(),
        )
        for index in range(10_000)
    ]
    return Fixture(
        settings={"directory": r"C:\Downloads\Archive"},
        tools=_tools(),
        links="\n".join(urls),
        events=events,
        history=history,
    )


def build(state: str) -> Fixture:
    return {"demo": _demo, "worst": _worst, "empty": _empty, "one": _one, "huge": _huge}[state]()
