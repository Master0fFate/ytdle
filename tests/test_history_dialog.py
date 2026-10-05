from collections import Counter

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QMessageBox

from core.history import HistoryRecord
from ui.components.history_dialog import PATH_COLUMN, HistoryDialog
from ui.styles import apply_chrome


class FakeHistory:
    def __init__(self, records):
        self.records = records
        self.calls = Counter()

    def get_all(self, limit=None):
        self.calls["get_all"] += 1
        return list(self.records)[:limit] if limit else list(self.records)

    def get_completed(self, limit=None):
        self.calls["get_completed"] += 1
        return [record for record in self.records if record.success]

    def get_failed(self, limit=None):
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
    assert dialog.completed_table.item(0, PATH_COLUMN).toolTip().startswith("C:/Downloads/")

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


def test_history_tabs_have_space_before_the_table(qtbot):
    apply_chrome(QApplication.instance())
    dialog = HistoryDialog(FakeHistory(_records(100)))
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.wait(20)

    tab_bar = dialog.tab_widget.tabBar()
    tab_bottom = tab_bar.mapTo(dialog, QPoint(0, tab_bar.height())).y()
    table_top = dialog.completed_table.mapTo(dialog, QPoint(0, 0)).y()
    assert table_top - tab_bottom >= 10
    assert dialog.completed_table.verticalScrollBar().isVisible()


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


def test_history_shows_readable_paths_reasons_titles_and_dates(qtbot):
    records = [
        HistoryRecord(
            url="https://example.test/a", title="", format="mp3", quality="320k",
            timestamp="1970-01-01T00:00:00", output_path="C:/Downloads/a.mp3",
            success=True, error_message="", retry_count=0,
        ),
        HistoryRecord(
            url="https://example.test/b", title="<b>Live</b>", format="mp4", quality="1080p",
            timestamp="", output_path="", success=False,
            error_message="ERROR: [site] b: Private video\nTraceback (most recent call last):",
            retry_count=0,
        ),
    ]
    dialog = HistoryDialog(FakeHistory(records))
    qtbot.addWidget(dialog)

    assert dialog.completed_table.columnCount() == 6
    assert dialog.completed_table.item(0, 1).text() == "example.test/a"
    assert dialog.completed_table.item(0, 4).text() == "—"
    assert dialog.failed_table.item(0, PATH_COLUMN).text() == "[site] b: Private video"
    assert dialog.failed_table.item(0, 4).text() == "—"
    # Titles that look like HTML stay literal in tooltips.
    assert dialog.failed_table.item(0, 1).toolTip() == "<qt>&lt;b&gt;Live&lt;/b&gt;</qt>"


def test_long_history_opens_with_the_newest_page_and_can_load_all(qtbot, monkeypatch):
    import ui.components.history_dialog as history_dialog

    monkeypatch.setattr(history_dialog, "PAGE_SIZE", 50)
    dialog = HistoryDialog(FakeHistory(_records(120)))
    qtbot.addWidget(dialog)
    assert dialog.completed_table.rowCount() + dialog.failed_table.rowCount() == 50
    assert dialog.tab_widget.tabText(1).endswith("+)")
    assert not dialog.load_all_btn.isHidden()

    dialog.load_all_btn.click()
    assert dialog.completed_table.rowCount() + dialog.failed_table.rowCount() == 120
    assert dialog.load_all_btn.isHidden()
