import pytest

from core.async_manager import AsyncDownloadManager, DownloadItemContext
from core.config import DownloadOptions
from core.downloader import DownloadManager


def _options(tmp_path):
    return DownloadOptions(
        is_mp3=False,
        quality="1080p",
        outtmpl_template="%(title)s",
        directory=str(tmp_path),
        download_playlist=False,
        restrict_filenames=False,
    )


def _exercise_stream(hook):
    downloading = {
        "status": "downloading",
        "total_bytes": 100,
        "downloaded_bytes": 0,
        "speed": 2_000_000,
        "eta": 10,
    }
    for downloaded in (0, 0, 0, 50, 50, 100, 100):
        downloading["downloaded_bytes"] = downloaded
        hook(downloading)
    hook({"status": "finished", "filename": "C:/Downloads/video.mp4"})


def test_sync_progress_coalesces_only_exact_duplicates_and_forces_terminal(tmp_path):
    progress = []
    statuses = []
    logs = []
    manager = DownloadManager(
        [],
        _options(tmp_path),
        on_progress=progress.append,
        on_status=statuses.append,
        on_log=logs.append,
    )

    _exercise_stream(manager._progress_hook)

    assert progress == [0, 50, 100, 100]
    assert statuses == ["Downloading... 1.9 MB/s | ETA 0:10", "Processing downloaded file..."]
    assert logs[-1] == "Download finished. Running post-processing..."

    manager.cancel()
    with pytest.raises(RuntimeError, match="User cancelled"):
        manager._progress_hook({"status": "downloading"})


def test_async_progress_coalesces_per_item_and_forces_terminal(tmp_path):
    progress = []
    statuses = []
    logs = []
    manager = AsyncDownloadManager(
        [],
        _options(tmp_path),
        on_progress=progress.append,
        on_status=statuses.append,
        on_log=logs.append,
        max_concurrent=1,
    )
    context = DownloadItemContext("https://example.test/video")
    manager._thread_local.context = context
    try:
        _exercise_stream(manager._progress_hook)

        assert progress == [0, 50, 100, 100]
        assert statuses == [
            "Downloading... 1.9 MB/s | ETA 0:10",
            "Processing downloaded file...",
        ]
        assert logs[-1] == "Download finished. Running post-processing..."

        manager.cancel()
        with pytest.raises(RuntimeError, match="User cancelled"):
            manager._progress_hook({"status": "downloading"})
    finally:
        manager._executor.shutdown(wait=True)
