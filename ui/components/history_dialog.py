from datetime import datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)

from core.history import DownloadHistory
from ui.components.session_list import display_url
from ui.icons import line_icon
from ui.skins import active_skin
from ui.styles import strip_native_frames
from ui.text import count, plain_tip

# Opening history stays fast however long it grows; "Load all" lifts the cap.
PAGE_SIZE = 2000
_COLUMNS = ("URL", "Title", "Format", "Quality", "Date", "Saved to / Reason")
PATH_COLUMN = 5


def _first_line(message: str) -> str:
    lines = message.strip().removeprefix("ERROR:").strip().splitlines()
    return lines[0] if lines else ""


class HistoryDialog(QDialog):
    def __init__(self, history: DownloadHistory, parent=None):
        super().__init__(parent)
        self._history = history
        self._limit = PAGE_SIZE
        self._truncated = False
        self.setObjectName("HistoryDialog")
        self.setModal(True)
        self.setWindowTitle("Download history")
        self.setMinimumSize(720, 480)
        self.resize(900, 600)

        self._init_ui()
        strip_native_frames(self)
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # The tabs already split by status, so search is the only filter.
        header = QHBoxLayout()
        header.setSpacing(12)
        title = QLabel("Download history", self)
        title.setObjectName("DialogTitle")
        header.addWidget(title)
        header.addStretch()
        self.filter_input = QLineEdit(self)
        self.filter_input.setAccessibleName("Filter download history")
        self.filter_input.setPlaceholderText("Search title, link, or quality")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.setMinimumWidth(300)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        header.addWidget(self.filter_input)
        layout.addLayout(header)

        self.tab_widget = QTabWidget(self)

        self.completed_table = QTableWidget(self)
        self._setup_table(self.completed_table)

        self.failed_table = QTableWidget(self)
        self._setup_table(self.failed_table)

        self.tab_widget.addTab(self.completed_table, "Completed")
        self.tab_widget.addTab(self.failed_table, "Failed")
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # Destructive and batch actions carry words, not just glyphs.
        self.clear_completed_btn = self._action_button(
            "Clear completed", "clear", "Delete every completed record from history"
        )
        self.clear_completed_btn.clicked.connect(self._clear_completed)
        button_layout.addWidget(self.clear_completed_btn)

        self.clear_failed_btn = self._action_button(
            "Clear failed", "clear", "Delete every failed record from history"
        )
        self.clear_failed_btn.clicked.connect(self._clear_failed)
        button_layout.addWidget(self.clear_failed_btn)

        self.load_all_btn = self._action_button(
            "Load all", "history", "Show every record, not only the newest"
        )
        self.load_all_btn.clicked.connect(self._load_all)
        button_layout.addWidget(self.load_all_btn)
        self.note_label = QLabel("", self)
        self.note_label.setObjectName("HistoryNote")
        button_layout.addWidget(self.note_label)
        button_layout.addStretch()

        self.export_failed_btn = self._action_button(
            "Export failed", "import", "Save failed links to a text file"
        )
        self.export_failed_btn.clicked.connect(self._export_failed_urls)
        self.export_failed_btn.setEnabled(False)
        button_layout.addWidget(self.export_failed_btn)

        self.retry_failed_btn = self._action_button(
            "Retry failed", "resume", "Add failed links back to the download list"
        )
        self.retry_failed_btn.clicked.connect(self._retry_failed)
        self.retry_failed_btn.setEnabled(False)
        button_layout.addWidget(self.retry_failed_btn)

        self.close_btn = QPushButton(self._words("Close"), self)
        self.close_btn.setAccessibleName("Close history")
        self.close_btn.setMinimumWidth(80)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self._selected_urls_for_retry = []

    @staticmethod
    def _words(text: str) -> str:
        return text if active_skin().icon_actions else f"[{text.lower()}]"

    def _action_button(self, text: str, icon: str, tip: str) -> QPushButton:
        button = QPushButton(self._words(text), self)
        if active_skin().icon_actions:
            button.setIcon(line_icon(icon))
            button.setIconSize(QSize(18, 18))
        button.setToolTip(tip)
        button.setAccessibleName(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _update_tab_counts(self):
        more = "+" if self._truncated else ""
        self.tab_widget.setTabText(0, f"Completed ({count(len(self._completed_records))}{more})")
        self.tab_widget.setTabText(1, f"Failed ({count(len(self._failed_records))}{more})")
        self.load_all_btn.setVisible(self._truncated)
        self.note_label.setVisible(self._truncated)
        self.note_label.setText(f"Newest {count(self._limit)} shown" if self._truncated else "")

    def _setup_table(self, table: QTableWidget):
        table.setColumnCount(len(_COLUMNS))
        table.setHorizontalHeaderLabels(list(_COLUMNS))
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        # Long links would otherwise squeeze the title; cap the URL column instead.
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.resizeSection(0, 220)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for column in (2, 3, 4):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(PATH_COLUMN, QHeaderView.Stretch)
        # Paths and links differ at the end (file name, video id): keep both ends.
        table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        table.setWordWrap(False)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

    def _load_data(self):
        records = self._history.get_all(self._limit + 1) if self._limit else self._history.get_all()
        self._truncated = bool(self._limit) and len(records) > self._limit
        if self._truncated:
            records = records[: self._limit]
        self._completed_records = [record for record in records if record.success]
        self._failed_records = [record for record in records if not record.success]
        self._populate_table(self.completed_table, self._completed_records)
        self._populate_table(self.failed_table, self._failed_records)
        self._sync_actions()

    def _load_all(self):
        self._limit = 0
        self._load_data()

    def _load_completed(self):
        self._completed_records = self._history.get_completed(self._limit or None)
        self._populate_table(self.completed_table, self._completed_records)
        self._sync_actions()

    def _load_failed(self):
        self._failed_records = self._history.get_failed(self._limit or None)
        self._populate_table(self.failed_table, self._failed_records)
        self._sync_actions()

    def _sync_actions(self):
        has_failed = bool(self._failed_records)
        self.export_failed_btn.setEnabled(has_failed)
        self.retry_failed_btn.setEnabled(has_failed)
        self.clear_failed_btn.setEnabled(has_failed)
        self.clear_completed_btn.setEnabled(bool(self._completed_records))
        self._update_tab_counts()
        if self.filter_input.text():
            self._on_filter_changed()

    def _populate_table(self, table: QTableWidget, records):
        sorting_enabled = table.isSortingEnabled()
        header = table.horizontalHeader()
        sort_section = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()
        table.setUpdatesEnabled(False)
        table.setSortingEnabled(False)
        try:
            table.clearContents()
            table.setRowCount(len(records))
            set_item = table.setItem

            for idx, record in enumerate(records):
                table.setRowHidden(idx, False)
                url_item = QTableWidgetItem(record.url)
                url_item.setToolTip(plain_tip(record.url))
                url_item.setData(
                    Qt.ItemDataRole.UserRole,
                    (
                        record.url.lower(),
                        record.title.lower(),
                        record.format.lower(),
                        record.quality.lower(),
                    ),
                )
                set_item(idx, 0, url_item)

                title = record.title.strip()
                if not title or title == "Unknown":
                    # Failed before yt-dlp learned the title: the link says more.
                    title = display_url(record.url)
                title_item = QTableWidgetItem(title)
                title_item.setToolTip(plain_tip(title))
                set_item(idx, 1, title_item)

                set_item(idx, 2, QTableWidgetItem(record.format))
                set_item(idx, 3, QTableWidgetItem(record.quality))
                set_item(idx, 4, QTableWidgetItem(self._format_date(record.timestamp)))

                if record.success:
                    path_item = QTableWidgetItem(record.output_path or "—")
                    path_item.setToolTip(plain_tip(record.output_path or ""))
                    set_item(idx, PATH_COLUMN, path_item)
                else:
                    error_item = QTableWidgetItem(_first_line(record.error_message) or "—")
                    error_item.setToolTip(plain_tip(record.error_message))
                    set_item(idx, PATH_COLUMN, error_item)
        finally:
            table.setSortingEnabled(sorting_enabled)
            if sorting_enabled and sort_section >= 0:
                table.sortItems(sort_section, sort_order)
            table.setUpdatesEnabled(True)

    @staticmethod
    def _format_date(timestamp) -> str:
        """Local date and minute; '—' when the time is missing or the Unix epoch."""
        try:
            moment = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp))
        except (TypeError, ValueError):
            return "—"
        if moment.year < 2000:
            return "—"
        return moment.strftime("%Y-%m-%d %H:%M")

    def _on_filter_changed(self):
        table = self.tab_widget.currentWidget()
        self._filter_table(table, self.filter_input.text().lower())

    def _filter_table(self, table: QTableWidget, filter_text: str):
        table.setUpdatesEnabled(False)
        try:
            for row in range(table.rowCount()):
                search_fields = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                table.setRowHidden(
                    row, not any(filter_text in field for field in search_fields)
                )
        finally:
            table.setUpdatesEnabled(True)

    def _on_tab_changed(self, _index: int):
        # Keep the search when switching tabs; apply it to the visible table.
        self._on_filter_changed()

    def _export_failed_urls(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Failed URLs",
            "failed_urls.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            if self._history.export_failed(file_path):
                QMessageBox.information(self, "Export Successful", f"Failed URLs exported to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export URLs. Check file permissions.")

    def _retry_failed(self):
        failed_urls = self._history.get_failed_urls()

        if not failed_urls:
            QMessageBox.information(self, "No Failed URLs", "There are no failed URLs to retry.")
            return

        noun = "link" if len(failed_urls) == 1 else "links"
        confirm = QMessageBox.question(
            self,
            "Retry Failed Downloads",
            f"{count(len(failed_urls))} failed {noun}.\n\nAdd them to the download list?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self._selected_urls_for_retry = failed_urls
            self.accept()

    def _clear_completed(self):
        confirm = QMessageBox.question(
            self,
            "Clear Completed History",
            "Are you sure you want to clear all completed download history?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self._history.clear_completed()
            self._load_completed()

    def _clear_failed(self):
        confirm = QMessageBox.question(
            self,
            "Clear Failed History",
            "Are you sure you want to clear all failed download history?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            self._history.clear_failed()
            self._load_failed()

    def get_retry_urls(self) -> list[str]:
        return self._selected_urls_for_retry
