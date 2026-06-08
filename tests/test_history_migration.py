import json
from pathlib import Path

from core.history import DownloadHistory


def test_history_migrates_legacy_list_json(tmp_path: Path):
    history_file = tmp_path / "history.json"
    history_file.write_text(
        json.dumps([
            {
                "url": "https://example.com/video",
                "title": "Example",
                "format": "mp4",
                "quality": "1080p",
                "timestamp": "2026-01-01T00:00:00",
                "output_path": "C:/Downloads/example.mp4",
                "success": True,
                "error_message": "",
                "retry_count": 0,
            }
        ]),
        encoding="utf-8",
    )

    history = DownloadHistory(str(history_file))

    completed = history.get_completed()
    assert len(completed) == 1
    assert completed[0].url == "https://example.com/video"
    assert (tmp_path / "history.json.backup").exists()
