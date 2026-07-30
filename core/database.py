"""
SQLite-based history management for scalable data persistence.

Replaces JSON-based storage with SQLite for O(1) / O(log n) operations
instead of O(n) read/write for large history files.
"""

import sqlite3
import json
import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class HistoryRecord:
    """Represents a single download history record."""
    id: int
    url: str
    title: str
    format: str
    quality: str
    timestamp: datetime
    output_path: str
    success: bool
    error_message: str
    retry_count: int
    metadata: Dict[str, Any]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "HistoryRecord":
        """Create a HistoryRecord from a database row."""
        metadata = {}
        metadata_text = row["metadata"]
        if metadata_text and metadata_text != "{}":
            try:
                metadata = json.loads(metadata_text)
            except json.JSONDecodeError:
                pass

        return cls(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            format=row["format"],
            quality=row["quality"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            output_path=row["output_path"],
            success=bool(row["success"]),
            error_message=row["error_message"] or "",
            retry_count=row["retry_count"],
            metadata=metadata
        )


class DatabaseManager:
    """
    Manages SQLite database for download history.

    Features:
    - WAL mode for better concurrency (single-writer/multi-reader)
    - Indexed queries for fast lookups
    - Automatic migration from JSON history
    - Context manager for safe connections
    """

    def __init__(self, db_path: Optional[str] = None, pool_size: int = 4):
        """
        Initialize the database manager.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.ytdle/ytdle.db
            pool_size: Maximum number of idle connections retained for reuse.
        """
        if db_path is None:
            ytdle_dir = Path.home() / ".ytdle"
            ytdle_dir.mkdir(parents=True, exist_ok=True)
            db_path = ytdle_dir / "ytdle.db"
        if pool_size < 1:
            raise ValueError("pool_size must be at least 1")

        self.db_path = str(db_path)
        self._pool_size = pool_size
        self._pool_condition = threading.Condition()
        self._connections: list[sqlite3.Connection] = []
        self._available: list[sqlite3.Connection] = []
        self._active_connections = 0
        self._closed = False
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self.get_connection() as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")

            # Create history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT DEFAULT 'Unknown',
                    format TEXT DEFAULT 'mp4',
                    quality TEXT DEFAULT 'best',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    output_path TEXT DEFAULT '',
                    success BOOLEAN DEFAULT 0,
                    error_message TEXT DEFAULT '',
                    retry_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_success ON history(success)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_url ON history(url)
            """)

            # Create settings table for app state
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            logger.info(f"Database initialized at {self.db_path}")

    def _create_connection(self) -> sqlite3.Connection:
        """Create one pool connection with connection-local durability settings."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=5.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _acquire_connection(self) -> sqlite3.Connection:
        """Exclusively check out a connection; never share one concurrently."""
        with self._pool_condition:
            if self._closed:
                raise RuntimeError("DatabaseManager is closed")
            if self._available:
                conn = self._available.pop()
            else:
                conn = self._create_connection()
                self._connections.append(conn)
            self._active_connections += 1
            return conn

    def _release_connection(
        self,
        conn: sqlite3.Connection,
        *,
        discard: bool = False,
    ) -> None:
        with self._pool_condition:
            self._active_connections -= 1
            if self._closed or discard or len(self._available) >= self._pool_size:
                try:
                    conn.close()
                finally:
                    self._connections.remove(conn)
            else:
                self._available.append(conn)
            self._pool_condition.notify_all()

    @contextmanager
    def get_connection(self):
        """
        Check out an exclusive pooled connection and commit before returning.

        Every connection receives the same connection-local SQLite pragmas.
        Exceptions roll back the current transaction before the connection is
        returned to the pool.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = self._acquire_connection()
        discard = False
        try:
            yield conn
            conn.commit()
        except BaseException:
            try:
                conn.rollback()
            except sqlite3.Error:
                discard = True
                logger.exception("Failed to roll back database transaction")
            raise
        finally:
            self._release_connection(conn, discard=discard)

    def close(self) -> None:
        """Close every pooled connection; safe to call more than once."""
        with self._pool_condition:
            if not self._closed:
                self._closed = True
                for conn in self._available:
                    try:
                        conn.close()
                    finally:
                        self._connections.remove(conn)
                self._available.clear()
                self._pool_condition.notify_all()

            while self._active_connections:
                self._pool_condition.wait()

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def migrate_from_json(self, json_path: Optional[str] = None) -> int:
        """
        Migrate history from JSON file to SQLite.

        Args:
            json_path: Path to JSON history file. Defaults to ~/.ytdle/history.json

        Returns:
            Number of records migrated
        """
        if json_path is None:
            json_path = Path.home() / ".ytdle" / "history.json"
        else:
            json_path = Path(json_path)

        if not json_path.exists():
            logger.info(f"No JSON history file found at {json_path}")
            return 0

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Support both legacy list format and dict-with-records format.
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get("records", [])
            else:
                logger.warning(f"Unexpected JSON history format at {json_path}; skipping migration")
                return 0

            migrated = 0

            with self.get_connection() as conn:
                for record in records:
                    try:
                        if not isinstance(record, dict):
                            logger.warning("Skipping invalid history record (expected object)")
                            continue
                        conn.execute("""
                            INSERT INTO history
                            (url, title, format, quality, timestamp, output_path,
                             success, error_message, retry_count, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.get("url", ""),
                            record.get("title", "Unknown"),
                            record.get("format", "mp4"),
                            record.get("quality", "best"),
                            record.get("timestamp", datetime.now().isoformat()),
                            record.get("output_path", ""),
                            record.get("success", False),
                            record.get("error_message", ""),
                            record.get("retry_count", 0),
                            json.dumps(record.get("metadata", {}))
                        ))
                        migrated += 1
                    except Exception as e:
                        logger.warning(f"Failed to migrate record: {e}")

            logger.info(f"Migrated {migrated} records from JSON")

            # Backup original JSON
            backup_path = json_path.with_suffix(".json.backup")
            json_path.rename(backup_path)
            logger.info(f"Backed up original JSON to {backup_path}")

            return migrated

        except Exception as e:
            logger.error(f"Failed to migrate from JSON: {e}")
            return 0

    def add_record(
        self,
        url: str,
        title: str,
        format: str,
        quality: str,
        output_path: str,
        success: bool,
        error_message: str = "",
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a new history record.

        Returns:
            ID of the inserted record
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO history
                (url, title, format, quality, output_path, success,
                 error_message, retry_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url, title, format, quality, output_path, success,
                error_message, retry_count, json.dumps(metadata or {})
            ))
            return cursor.lastrowid

    def add_completed(
        self,
        url: str,
        title: str,
        format: str,
        quality: str,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a completed download record."""
        return self.add_record(
            url=url,
            title=title,
            format=format,
            quality=quality,
            output_path=output_path,
            success=True,
            metadata=metadata
        )

    def add_failed(
        self,
        url: str,
        title: str,
        format: str,
        quality: str,
        error_message: str,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a failed download record."""
        return self.add_record(
            url=url,
            title=title,
            format=format,
            quality=quality,
            output_path="",
            success=False,
            error_message=error_message,
            retry_count=retry_count,
            metadata=metadata
        )

    def get_all(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get all history records, optionally limited."""
        with self.get_connection() as conn:
            query = "SELECT * FROM history ORDER BY timestamp DESC"
            params = ()

            if limit is not None:
                query += " LIMIT ?"
                params = (limit,)

            cursor = conn.execute(query, params)
            return [HistoryRecord.from_row(row) for row in cursor.fetchall()]

    def get_completed(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get completed download records."""
        with self.get_connection() as conn:
            query = "SELECT * FROM history WHERE success = 1 ORDER BY timestamp DESC"
            params = ()

            if limit is not None:
                query += " LIMIT ?"
                params = (limit,)

            cursor = conn.execute(query, params)
            return [HistoryRecord.from_row(row) for row in cursor.fetchall()]

    def get_failed(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get failed download records."""
        with self.get_connection() as conn:
            query = "SELECT * FROM history WHERE success = 0 ORDER BY timestamp DESC"
            params = ()

            if limit is not None:
                query += " LIMIT ?"
                params = (limit,)

            cursor = conn.execute(query, params)
            return [HistoryRecord.from_row(row) for row in cursor.fetchall()]

    def update_record(self, record_id: int, **kwargs) -> bool:
        """
        Update an existing record by primary key ID.

        Args:
            record_id: Record ID to match
            **kwargs: Fields to update

        Returns:
            True if record was updated
        """
        allowed_fields = {
            "title", "format", "quality", "output_path",
            "success", "error_message", "retry_count", "metadata"
        }

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        if "metadata" in updates and isinstance(updates["metadata"], dict):
            updates["metadata"] = json.dumps(updates["metadata"])

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())

        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE history SET {set_clause} WHERE id = ?",
                (*updates.values(), record_id)
            )
            return cursor.rowcount > 0

    def get_latest_by_url(self, url: str) -> Optional[HistoryRecord]:
        """Return the latest history record for an exact URL match."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM history WHERE url = ? ORDER BY id DESC LIMIT 1",
                (url,)
            ).fetchone()
            return HistoryRecord.from_row(row) if row else None

    def delete_record(self, record_id: int) -> bool:
        """Delete a record by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def clear_history(self) -> int:
        """Clear all history records."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM history")
            return cursor.rowcount

    def clear_completed(self) -> int:
        """Clear completed records."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM history WHERE success = 1")
            return cursor.rowcount

    def clear_failed(self) -> int:
        """Clear failed records."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM history WHERE success = 0")
            return cursor.rowcount

    def search(self, query: str, limit: int = 100) -> List[HistoryRecord]:
        """Search history records by URL or title."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM history
                WHERE url LIKE ? OR title LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            return [HistoryRecord.from_row(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        with self.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM history WHERE success = 1"
            ).fetchone()[0]
            failed = conn.execute(
                "SELECT COUNT(*) FROM history WHERE success = 0"
            ).fetchone()[0]

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "success_rate": completed / total if total > 0 else 0
            }

    def export_failed_urls(self, output_path: str) -> int:
        """Export failed URLs to a text file."""
        failed = self.get_failed()

        with open(output_path, "w", encoding="utf-8") as f:
            for record in failed:
                f.write(f"{record.url}\n")

        return len(failed)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,)
            ).fetchone()
            return json.loads(row["value"]) if row else default

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )


# Backward-compatible wrapper that mimics the old DownloadHistory API
class DownloadHistory:
    """
    Backward-compatible wrapper around DatabaseManager.

    Maintains the same API as the old JSON-based DownloadHistory
    while using SQLite for storage.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db = DatabaseManager(db_path)
        # Attempt migration on first run
        self._db.migrate_from_json()

    def add_completed(self, url: str, title: str, format: str, quality: str,
                      output_path: str) -> None:
        """Add a completed download record."""
        self._db.add_completed(url, title, format, quality, output_path)

    def add_failed(self, url: str, title: str, format: str, quality: str,
                   error_message: str) -> None:
        """Add a failed download record."""
        self._db.add_failed(url, title, format, quality, error_message)

    def get_completed(self, limit: Optional[int] = None) -> List[Dict]:
        """Get completed downloads as dicts (for backward compatibility)."""
        records = self._db.get_completed(limit)
        return [self._record_to_dict(r) for r in records]

    def get_failed(self, limit: Optional[int] = None) -> List[Dict]:
        """Get failed downloads as dicts (for backward compatibility)."""
        records = self._db.get_failed(limit)
        return [self._record_to_dict(r) for r in records]

    def get_all(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all downloads as dicts (for backward compatibility)."""
        records = self._db.get_all(limit)
        return [self._record_to_dict(r) for r in records]

    def update_record(self, url: str, **kwargs) -> bool:
        """Update the latest matching URL record (backward-compatible behavior)."""
        record = self._db.get_latest_by_url(url)
        if not record:
            return False
        return self._db.update_record(record.id, **kwargs)

    def clear_history(self) -> None:
        """Clear all history."""
        self._db.clear_history()

    def clear_completed(self) -> None:
        """Clear completed records."""
        self._db.clear_completed()

    def clear_failed(self) -> None:
        """Clear failed records."""
        self._db.clear_failed()

    def close(self) -> None:
        """Release database resources deterministically."""
        self._db.close()

    def export_failed(self, output_path: str) -> int:
        """Export failed URLs to a file."""
        return self._db.export_failed_urls(output_path)

    def _record_to_dict(self, record: HistoryRecord) -> Dict:
        """Convert HistoryRecord to dict for backward compatibility."""
        return {
            "url": record.url,
            "title": record.title,
            "format": record.format,
            "quality": record.quality,
            "timestamp": record.timestamp.isoformat(),
            "output_path": record.output_path,
            "success": record.success,
            "error_message": record.error_message,
            "retry_count": record.retry_count,
        }
