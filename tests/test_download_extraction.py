import asyncio
from collections.abc import Iterator
from typing import Any

import pytest

import core.async_manager as async_manager
import core.downloader as downloader
from core.config import DownloadOptions


def _options(tmp_path) -> DownloadOptions:
    return DownloadOptions(
        is_mp3=False,
        quality="1080p",
        outtmpl_template="%(title).150s",
        directory=str(tmp_path),
        download_playlist=False,
        restrict_filenames=False,
    )


class FakeYoutubeDL:
    responses: Iterator[dict[str, Any] | Exception]
    extract_calls: list[tuple[str, bool]]
    instance_count: int
    post_hook_path: str | None

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options
        type(self).instance_count += 1

    def __enter__(self) -> "FakeYoutubeDL":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def extract_info(self, url: str, *, download: bool) -> dict[str, Any]:
        type(self).extract_calls.append((url, download))
        response = next(type(self).responses)
        if isinstance(response, Exception):
            raise response
        if type(self).post_hook_path:
            for hook in self.options.get("post_hooks", ()):
                hook(type(self).post_hook_path)
        return response

    @classmethod
    def configure(
        cls,
        *responses: dict[str, Any] | Exception,
        post_hook_path: str | None = None,
    ) -> None:
        cls.responses = iter(responses)
        cls.extract_calls = []
        cls.instance_count = 0
        cls.post_hook_path = post_hook_path


@pytest.mark.parametrize(
    ("info", "expected_title"),
    [
        (
            {"title": "Single video", "uploader": "Creator", "duration": 61},
            "Single video",
        ),
        (
            {
                "_type": "playlist",
                "title": "Saved playlist",
                "entries": [{"title": "First"}, {"title": "Second"}],
            },
            "Saved playlist",
        ),
    ],
)
def test_sync_download_extracts_once_and_keeps_title(
    monkeypatch,
    tmp_path,
    info: dict[str, Any],
    expected_title: str,
):
    FakeYoutubeDL.configure(info)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    manager = downloader.DownloadManager([], _options(tmp_path))

    success, error = manager._download_with_fallback("https://example.test/media")

    assert (success, error) == (True, "")
    assert manager._current_title == expected_title
    assert FakeYoutubeDL.extract_calls == [("https://example.test/media", True)]
    assert FakeYoutubeDL.instance_count == 1


def test_sync_records_yt_dlp_postprocessed_filepath(monkeypatch, tmp_path):
    final_path = tmp_path / "converted.mp3"
    FakeYoutubeDL.configure(
        {
            "title": "Converted audio",
            "duration": 10,
            "filepath": str(tmp_path / "deleted-intermediate.webm"),
        },
        post_hook_path=str(final_path),
    )
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    manager = downloader.DownloadManager([], _options(tmp_path))

    success, error = manager._download_with_fallback("https://example.test/audio")

    assert (success, error) == (True, "")
    assert manager._current_output_file == str(final_path)
    assert str(final_path) in manager._artifact_candidates


def test_sync_format_fallback_uses_one_extraction_per_attempt(monkeypatch, tmp_path):
    FakeYoutubeDL.configure(
        RuntimeError("format not available"),
        {"title": "Fallback video", "duration": 30},
    )
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    manager = downloader.DownloadManager([], _options(tmp_path))

    success, error = manager._download_with_fallback("https://example.test/fallback")

    assert (success, error) == (True, "format not available")
    assert manager._current_title == "Fallback video"
    assert FakeYoutubeDL.extract_calls == [
        ("https://example.test/fallback", True),
        ("https://example.test/fallback", True),
    ]


def test_async_records_yt_dlp_postprocessed_filepath(monkeypatch, tmp_path):
    final_path = tmp_path / "merged.mp4"
    info = {
        "title": "Merged video",
        "duration": 10,
        "filepath": str(tmp_path / "deleted-intermediate.webm"),
    }
    FakeYoutubeDL.configure(info, post_hook_path=str(final_path))
    monkeypatch.setattr(async_manager.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    manager = async_manager.AsyncDownloadManager(
        [], _options(tmp_path), max_concurrent=1
    )
    context = async_manager.DownloadItemContext(url="https://example.test/video")

    try:
        success, error = asyncio.run(
            manager._download_with_fallback(context.url, context)
        )
    finally:
        manager._executor.shutdown(wait=True)

    assert (success, error) == (True, "")
    assert context.current_output_file == str(final_path)
    assert str(final_path) in context.artifact_candidates


def test_async_download_extracts_once_and_keeps_playlist_title(monkeypatch, tmp_path):
    info = {
        "_type": "playlist",
        "title": "Async playlist",
        "entries": [{"title": "First"}],
    }
    FakeYoutubeDL.configure(info)
    monkeypatch.setattr(async_manager.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    manager = async_manager.AsyncDownloadManager(
        [], _options(tmp_path), max_concurrent=1
    )
    context = async_manager.DownloadItemContext(url="https://example.test/playlist")

    try:
        manager._run_yt_dlp(context.url, {}, context)
    finally:
        manager._executor.shutdown(wait=True)

    assert context.current_title == "Async playlist"
    assert FakeYoutubeDL.extract_calls == [(context.url, True)]
    assert FakeYoutubeDL.instance_count == 1
