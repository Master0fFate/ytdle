from collections import Counter

from PySide6.QtWidgets import QMessageBox

from core.history import HistoryRecord
from ui.components.history_dialog import HistoryDialog


class FakeHistory:
    def __init__(self, records):
        self.records = records
        self.calls = Counter()

    def get_all(self):
        self.calls["get_all"] += 1
        return list(self.records)

    def get_completed(self):
        self.calls["get_completed"] += 1
        return [record for record in self.records if record.success]

    def get_failed(self):
        self.calls["get_failed"] += 1
        return [record for record in self.records if not record.success]

    def clear_completed(self):
        self.calls["clear_completed"] += 1
        self.records = [record for record in self.records if not record.success]

    def clear_failed(self):
        self.calls["clear_failed"] += 1
        self.records = [record for record in self.records if record.success]


def _records(count=500):
    return [
        HistoryRecord(
            url=f"https://example.test/{index}",
            title=f"Title {index}",
            format="mp4",
            quality="1080p",
            timestamp=f"2026-01-{(index % 28) + 1:02d}T12:34:56",
            output_path=f"C:/Downloads/{index}.mp4" if index % 3 else "",
            success=index % 3 != 0,
            error_message="" if index % 3 else f"Failure {index}",
            retry_count=index % 2,
        )
        for index in range(count)
    ]


def _visible_rows(table):
    return sum(not table.isRowHidden(row) for row in range(table.rowCount()))


def test_initial_load_queries_once_and_filter_keeps_all_table_rows(qtbot):
    records = _records()
    history = FakeHistory(records)
    dialog = HistoryDialog(history)
    qtbot.addWidget(dialog)

    completed_count = sum(record.success for record in records)
    failed_count = len(records) - completed_count
    assert history.calls == Counter({"get_all": 1})
    assert dialog.completed_table.rowCount() == completed_count
    assert dialog.failed_table.rowCount() == failed_count
    assert dialog.completed_table.isSortingEnabled()
    assert dialog.failed_table.isSortingEnabled()
    assert dialog.completed_table.item(0, 6).toolTip().startswith("C:/Downloads/")

    dialog.filter_input.setText("title 49")
    expected_visible = sum(
        record.success and "title 49" in record.title.lower() for record in records
    )
    assert _visible_rows(dialog.completed_table) == expected_visible
    assert dialog.completed_table.rowCount() == completed_count
    assert history.calls == Counter({"get_all": 1})

    dialog.filter_input.clear()
    assert _visible_rows(dialog.completed_table) == completed_count
    assert history.calls == Counter({"get_all": 1})


def test_clear_refreshes_only_the_changed_history_partition(
    qtbot, monkeypatch
):
    history = FakeHistory(_records(30))
    dialog = HistoryDialog(history)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )

    failed_before = dialog.failed_table.rowCount()
    dialog._clear_completed()

    assert history.calls["clear_completed"] == 1
    assert history.calls["get_completed"] == 1
    assert history.calls["get_failed"] == 0
    assert dialog.completed_table.rowCount() == 0
    assert dialog.failed_table.rowCount() == failed_before
