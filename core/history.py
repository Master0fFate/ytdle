import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from pathlib import Path


@dataclass
class HistoryRecord:
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
    def __init__(self, history_file: Optional[str] = None):
        self._history_file = history_file or self._get_default_history_path()
        self._records: List[HistoryRecord] = []
        self._load()

    def _get_default_history_path(self) -> str:
        app_dir = Path.home() / ".ytdle"
        app_dir.mkdir(exist_ok=True)
        return str(app_dir / "history.json")

    def _load(self) -> None:
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._records = [HistoryRecord(**item) for item in data]
        except Exception:
            self._records = []

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._history_file), exist_ok=True)
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self._records], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_record(self, record: HistoryRecord) -> None:
        self._records.append(record)
        self._save()

    def add_completed(self, url: str, title: str, format: str, quality: str, output_path: str) -> None:
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
        completed = [r for r in self._records if r.success]
        completed.sort(key=lambda x: x.timestamp, reverse=True)
        return completed[:limit] if limit else completed

    def get_failed(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        failed = [r for r in self._records if not r.success]
        failed.sort(key=lambda x: x.timestamp, reverse=True)
        return failed[:limit] if limit else failed

    def get_all(self, limit: Optional[int] = None) -> List[HistoryRecord]:
        all_records = sorted(self._records, key=lambda x: x.timestamp, reverse=True)
        return all_records[:limit] if limit else all_records

    def export_failed(self, output_file: str) -> bool:
        try:
            failed = self.get_failed()
            with open(output_file, "w", encoding="utf-8") as f:
                for record in failed:
                    f.write(f"# Failed: {record.error_message}\n")
                    f.write(f"# Retry count: {record.retry_count}\n")
                    f.write(f"# Date: {record.timestamp}\n")
                    f.write(f"{record.url}\n\n")
            return True
        except Exception:
            return False

    def get_failed_urls(self) -> List[str]:
        return [r.url for r in self.get_failed()]

    def clear_history(self) -> None:
        self._records.clear()
        self._save()

    def clear_completed(self) -> None:
        self._records = [r for r in self._records if not r.success]
        self._save()

    def clear_failed(self) -> None:
        self._records = [r for r in self._records if r.success]
        self._save()

    def get_record_by_url(self, url: str) -> Optional[HistoryRecord]:
        for record in reversed(self._records):
            if record.url == url:
                return record
        return None

    def update_record(self, url: str, success: bool, output_path: str = "", error_message: str = "") -> bool:
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
