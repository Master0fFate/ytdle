import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from core.database import DatabaseManager


def test_commits_are_visible_and_pragmas_apply_to_every_connection(tmp_path: Path):
    db_path = tmp_path / "history.db"
    manager = DatabaseManager(str(db_path), pool_size=2)
    try:
        record_id = manager.add_completed(
            "https://example.test/visible",
            "Visible",
            "mp4",
            "1080p",
            "C:/Downloads/visible.mp4",
        )

        with sqlite3.connect(db_path) as external:
            row = external.execute(
                "SELECT id, title FROM history WHERE id = ?", (record_id,)
            ).fetchone()
        assert row == (record_id, "Visible")

        with manager.get_connection() as first:
            with manager.get_connection() as second:
                for connection in (first, second):
                    assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
                    assert connection.execute("PRAGMA synchronous").fetchone()[0] == 1
                    assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    finally:
        manager.close()


def test_pool_supports_cross_thread_readers_and_committed_writers(tmp_path: Path):
    manager = DatabaseManager(str(tmp_path / "concurrent.db"), pool_size=2)

    def write_batch(batch: int) -> None:
        for item in range(40):
            index = batch * 40 + item
            manager.add_completed(
                f"https://example.test/{index}",
                f"Title {index}",
                "mp4",
                "Best",
                f"C:/Downloads/{index}.mp4",
            )

    def read_repeatedly() -> None:
        for _ in range(25):
            stats = manager.get_stats()
            assert 0 <= stats["completed"] <= 160

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(write_batch, batch) for batch in range(4)]
            futures.extend(executor.submit(read_repeatedly) for _ in range(4))
            for future in futures:
                future.result()

        assert manager.get_stats() == {
            "total": 160,
            "completed": 160,
            "failed": 0,
            "success_rate": 1.0,
        }
    finally:
        manager.close()


def test_transaction_rolls_back_after_injected_failure(tmp_path: Path):
    manager = DatabaseManager(str(tmp_path / "rollback.db"))
    try:
        with pytest.raises(sqlite3.IntegrityError):
            with manager.get_connection() as connection:
                connection.execute(
                    "INSERT INTO history (url, title) VALUES (?, ?)",
                    ("https://example.test/rolled-back", "Rolled back"),
                )
                connection.execute("INSERT INTO history (url) VALUES (NULL)")

        assert manager.get_latest_by_url("https://example.test/rolled-back") is None
    finally:
        manager.close()


def test_close_waits_for_checkout_and_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "close.db"
    manager = DatabaseManager(str(db_path), pool_size=1)
    checked_out = threading.Event()
    release = threading.Event()
    close_finished = threading.Event()

    def hold_connection() -> None:
        with manager.get_connection() as connection:
            connection.execute(
                "INSERT INTO history (url, title) VALUES (?, ?)",
                ("https://example.test/durable", "Durable"),
            )
            checked_out.set()
            assert release.wait(5)

    def close_manager() -> None:
        manager.close()
        close_finished.set()

    holder = threading.Thread(target=hold_connection)
    closer = threading.Thread(target=close_manager)
    holder.start()
    assert checked_out.wait(5)
    closer.start()
    assert not close_finished.wait(0.05)
    release.set()
    holder.join(5)
    closer.join(5)

    assert not holder.is_alive()
    assert not closer.is_alive()
    assert close_finished.is_set()
    manager.close()
    with pytest.raises(RuntimeError, match="closed"):
        with manager.get_connection():
            pass

    with sqlite3.connect(db_path) as external:
        assert external.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 1
