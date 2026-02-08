"""
History management module - now backed by SQLite for better performance.

This module maintains backward compatibility with the old JSON-based API
while using SQLite for storage (O(1) / O(log n) operations vs O(n)).
"""

import json
import os
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Import database components
try:
    from core.database import DatabaseManager, HistoryRecord as DBHistoryRecord
    _HAS_SQLITE = True
except ImportError:
    _HAS_SQLITE = False


@dataclass
class HistoryRecord:
    """Legacy HistoryRecord for backward compatibility."""
    url: str
    title: str
    format: str
    quality: str
    timestamp: str
    output_path: str
    success: bool
    error_message: str = ""
    retry_count: int = 0


class DownloadHistory:
    """
    Download history manager with SQLite backend.

    Maintains full backward compatibility with the old JSON-based API
    while using SQLite for better performance with large history files.
    """

    def __init__(self, history_file: Optional[str] = None):
        self._history_file = history_file or self._get_default_history_path()
        self._records: List[HistoryRecord] = []

        # Use SQLite if available
        if _HAS_SQLITE:
            self._db = DatabaseManager()
            # Migrate from JSON on first run
            self._db.migrate_from_json(self._history_file)
            self._use_sqlite = True
        else:
            self._db = None
            self._use_sqlite = False
            # Fallback to JSON
            self._load()

    def _get_default_history_path(self) -> str:
        app_dir = Path.home() / ".ytdle"
        app_dir.mkdir(exist_ok=True)
        return str(app_dir / "history.json")

    def _load(self) -> None:
        """Load from JSON (fallback mode)."""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle both old format (list) and new format (dict with records)
                    if isinstance(data, list):
                        self._records = [HistoryRecord(**item) for item in data]
                    elif isinstance(data, dict) and "records" in data:
                        self._records = [HistoryRecord(**item) for item in data["records"]]
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            self._records = []

    def _save(self) -> None:
        """Save to JSON (fallback mode)."""
        if self._use_sqlite:
            return
        try:
            os.makedirs(os.path.dirname(self._history_file), exist_ok=True)
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self._records], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save history: {e}")

    def _db_record_to_history(self, record) -> HistoryRecord:
        """Convert database record to HistoryRecord."""
        return HistoryRecord(
            url=record.url,
            title=record.title,
            format=record.format,
            quality=record.quality,
            timestamp=record.timestamp.isoformat() if isinstance(record.timestamp, datetime) else str(record.timestamp),
            output_path=record.output_path,
            success=record.success,
            error_message=record.error_message,
            retry_count=record.retry_count
        )

    def add_record(self, record: HistoryRecord) -> None:
        """Add a history record."""
        if self._use_sqlite:
            self._db.add_record(
                url=record.url,
                title=record.title,
                format=record.format,
                quality=record.quality,
                output_path=record.output_path,
                success=record.success,
                error_message=record.error_message,
                retry_count=record.retry_count
            )
        else:
            self._records.append(record)
            self._save()

    def add_completed(self, url: str, title: str, format: str, quality: str, output_path: str) -> None:
        """Add a completed download record."""
        if self._use_sqlite:
            self._db.add_completed(
                url=url,
                title=title or "Unknown title",
                format=format,
                quality=quality,
                output_path=output_path or ""
            )
        else:
            record = HistoryRecord(
                url=url,
                title=title or "Unknown title",
                format=format,
                quality=quality,
                timestamp=datetime.now().isoformat(),
                output_path=output_path or "",
                success=True
            )
            self.add_record(record)

    def add_failed(self, url: str, title: str, format: str, quality: str, error_message: str, retry_count: int = 0) -> None:
        """Add a failed download record."""
        if self._use_sqlite:
            self._db.add_failed(
                url=url,
                title=title or "Unknown title",
                format=format,
                quality=quality,
                error_message=error_message,
                retry_count=retry_count
            )
        else:
            record = HistoryRecord(
                url=url,
                title=title or "Unknown title",
                format=format,
                quality=quality,
                timestamp=datetime.now().isoformat(),
                output_path="",
                success=False,
                error_message=error_message,
                retry_count=retry_count
            )
            self.add_record(record)

    def get_completed(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get completed downloads."""
        if self._use_sqlite:
            records = self._db.get_completed(limit)
            return [self._db_record_to_history(r) for r in records]
        else:
            completed = [r for r in self._records if r.success]
            completed.sort(key=lambda x: x.timestamp, reverse=True)
            return completed[:limit] if limit else completed

    def get_failed(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get failed downloads."""
        if self._use_sqlite:
            records = self._db.get_failed(limit)
            return [self._db_record_to_history(r) for r in records]
        else:
            failed = [r for r in self._records if not r.success]
            failed.sort(key=lambda x: x.timestamp, reverse=True)
            return failed[:limit] if limit else failed

    def get_all(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        """Get all downloads."""
        if self._use_sqlite:
            records = self._db.get_all(limit)
            return [self._db_record_to_history(r) for r in records]
        else:
            all_records = sorted(self._records, key=lambda x: x.timestamp, reverse=True)
            return all_records[:limit] if limit else all_records

    def export_failed(self, output_file: str) -> bool:
        """Export failed URLs to a text file."""
        try:
            failed = self.get_failed()
            with open(output_file, "w", encoding="utf-8") as f:
                for record in failed:
                    f.write(f"# Failed: {record.error_message}\n")
                    f.write(f"# Retry count: {record.retry_count}\n")
                    f.write(f"# Date: {record.timestamp}\n")
                    f.write(f"{record.url}\n\n")
            return True
        except Exception as e:
            logger.error(f"Failed to export failed URLs: {e}")
            return False

    def get_failed_urls(self) -> List[str]:
        """Get list of failed URLs."""
        return [r.url for r in self.get_failed()]

    def clear_history(self) -> None:
        """Clear all history."""
        if self._use_sqlite:
            self._db.clear_history()
        else:
            self._records.clear()
            self._save()

    def clear_completed(self) -> None:
        """Clear completed records."""
        if self._use_sqlite:
            self._db.clear_completed()
        else:
            self._records = [r for r in self._records if not r.success]
            self._save()

    def clear_failed(self) -> None:
        """Clear failed records."""
        if self._use_sqlite:
            self._db.clear_failed()
        else:
            self._records = [r for r in self._records if r.success]
            self._save()

    def get_record_by_url(self, url: str) -> Optional[HistoryRecord]:
        """Get a record by URL."""
        if self._use_sqlite:
            # Search in database
            results = self._db.search(url, limit=1)
            if results:
                return self._db_record_to_history(results[0])
            return None
        else:
            for record in reversed(self._records):
                if record.url == url:
                    return record
            return None

    def update_record(self, url: str, success: bool, output_path: str = "", error_message: str = "") -> bool:
        """Update an existing record."""
        if self._use_sqlite:
            record = self.get_record_by_url(url)
            if record:
                retry_count = record.retry_count
                if not success:
                    retry_count += 1
                return self._db.update_record(
                    url=url,
                    success=success,
                    output_path=output_path or record.output_path,
                    error_message=error_message or record.error_message,
                    retry_count=retry_count
                )
            return False
        else:
            record = self.get_record_by_url(url)
            if record:
                record.success = success
                if output_path:
                    record.output_path = output_path
                if error_message:
                    record.error_message = error_message
                if not success:
                    record.retry_count += 1
                self._save()
                return True
            return False

    def search(self, query: str, limit: int = 100) -> List[HistoryRecord]:
        """Search history by URL or title."""
        if self._use_sqlite:
            records = self._db.search(query, limit)
            return [self._db_record_to_history(r) for r in records]
        else:
            results = []
            query_lower = query.lower()
            for record in self._records:
                if query_lower in record.url.lower() or query_lower in record.title.lower():
                    results.append(record)
            return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        if self._use_sqlite:
            return self._db.get_stats()
        else:
            total = len(self._records)
            completed = len([r for r in self._records if r.success])
            failed = total - completed
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "success_rate": completed / total if total > 0 else 0
            }
