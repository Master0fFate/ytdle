"""Cancel, pause/resume, and skip against a fake yt-dlp run with real threads."""

import threading
import time
from collections import Counter

import pytest

from core.async_manager import AsyncDownloadManager
from core.config import DownloadOptions


def _options(tmp_path):
    return DownloadOptions(
        is_mp3=False,
        quality="1080p",
        outtmpl_template="%(title)s",
        directory=str(tmp_path),
        download_playlist=False,
        restrict_filenames=False,
    )


class _Harness:
    """Run a manager on its own thread with a fake, hook-driven transfer."""

    def __init__(self, monkeypatch, tmp_path, urls, *, max_concurrent=3, steps=20):
        self.calls = Counter()
        self.finished = []
        self.all_finished = threading.Event()
        self.manager = AsyncDownloadManager(
            urls,
            _options(tmp_path),
            on_item_finished=lambda url, ok, info: self.finished.append((url, ok, info)),
            on_all_finished=lambda *_counts: self.all_finished.set(),
            max_concurrent=max_concurrent,
        )

        def fake_run(_manager, url, ydl_opts, _ctx):
            self.calls[url] += 1
            hook = ydl_opts["progress_hooks"][0]
            for step in range(steps + 1):
                # Call from a separate thread, like yt-dlp's fragment workers do.
                errors = []
                worker = threading.Thread(target=self._call, args=(hook, step, steps, errors))
                worker.start()
                worker.join()
                if errors:
                    raise errors[0]
                time.sleep(0.01)

        monkeypatch.setattr(AsyncDownloadManager, "_run_yt_dlp", fake_run)
        self.thread = threading.Thread(target=self.manager.run, daemon=True)

    @staticmethod
    def _call(hook, step, steps, errors):
        try:
            hook({"status": "downloading", "total_bytes": steps, "downloaded_bytes": step})
        except Exception as error:  # noqa: BLE001 - re-raised in the executor thread
            errors.append(error)

    def wait(self, timeout=10):
        assert self.all_finished.wait(timeout), "batch never finished"
        self.thread.join(timeout)


def test_cancel_with_long_queue_finishes_the_batch(monkeypatch, tmp_path):
    urls = [f"https://example.test/{index}" for index in range(10)]
    harness = _Harness(monkeypatch, tmp_path, urls)
    harness.thread.start()
    time.sleep(0.05)
    harness.manager.cancel()
    harness.wait()
    assert all(info == "Cancelled" for _url, ok, info in harness.finished if not ok)


def test_resume_wakes_workers_paused_before_and_during_downloads(monkeypatch, tmp_path):
    urls = [f"https://example.test/{index}" for index in range(4)]
    harness = _Harness(monkeypatch, tmp_path, urls, max_concurrent=2)
    harness.thread.start()
    time.sleep(0.05)
    harness.manager.pause()
    time.sleep(0.4)
    paused_count = len(harness.finished)
    time.sleep(0.3)
    assert len(harness.finished) == paused_count, "running items must hold while paused"

    harness.manager.resume()
    harness.wait()
    assert sorted(url for url, ok, _info in harness.finished if ok) == urls


def test_skip_hits_only_running_items_and_never_retries(monkeypatch, tmp_path):
    urls = [f"https://example.test/{index}" for index in range(3)]
    harness = _Harness(monkeypatch, tmp_path, urls, max_concurrent=1)
    harness.thread.start()
    time.sleep(0.05)
    harness.manager.skip_current()
    harness.wait()

    results = {url: info for url, _ok, info in harness.finished}
    assert results[urls[0]] == "Skipped"
    assert results[urls[1]] != "Skipped"
    assert results[urls[2]] != "Skipped"
    assert harness.calls == Counter({url: 1 for url in urls})


@pytest.mark.parametrize("message", ["ERROR: Private video. Sign in", "HTTP Error 404: Not Found"])
def test_unrecoverable_errors_fail_without_retrying(monkeypatch, tmp_path, message):
    calls = Counter()

    def failing_run(_manager, url, _ydl_opts, _ctx):
        calls[url] += 1
        raise RuntimeError(message)

    monkeypatch.setattr(AsyncDownloadManager, "_run_yt_dlp", failing_run)
    finished = []
    manager = AsyncDownloadManager(
        ["https://example.test/a"],
        _options(tmp_path),
        on_item_finished=lambda url, ok, info: finished.append((ok, info)),
    )
    manager.run()
    assert calls["https://example.test/a"] == 1
    assert finished == [(False, message)]
