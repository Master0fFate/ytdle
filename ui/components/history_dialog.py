from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
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
    QDateEdit,
    QCheckBox,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QWidget,
    QComboBox,
    QDialogButtonBox,
)

from core.history import DownloadHistory


class HistoryDialog(QDialog):
    def __init__(self, history: DownloadHistory, parent=None):
        super().__init__(parent)
        self._history = history
        self.setObjectName("HistoryDialog")
        self.setModal(True)
        self.setMinimumSize(900, 600)

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Download History", self)
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header.addWidget(title)
        header.addStretch()

        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:", self)
        self.filter_input = QLineEdit(self)
        self.filter_input.setPlaceholderText("Search by title, URL, or quality...")
        self.filter_input.textChanged.connect(self._on_filter_changed)

        status_filter_layout = QHBoxLayout()
        status_label = QLabel("Status:", self)
        self.status_combo = QComboBox(self)
        self.status_combo.addItems(["All", "Completed", "Failed"])
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_input, 1)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_combo)

        layout.addLayout(header)
        layout.addLayout(filter_layout)

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
        button_layout.addStretch()

        self.export_failed_btn = QPushButton("Export Failed URLs", self)
        self.export_failed_btn.clicked.connect(self._export_failed_urls)
        self.export_failed_btn.setEnabled(False)
        button_layout.addWidget(self.export_failed_btn)

        self.retry_failed_btn = QPushButton("Retry Failed", self)
        self.retry_failed_btn.clicked.connect(self._retry_failed)
        self.retry_failed_btn.setEnabled(False)
        button_layout.addWidget(self.retry_failed_btn)

        self.clear_completed_btn = QPushButton("Clear Completed", self)
        self.clear_completed_btn.clicked.connect(self._clear_completed)
        button_layout.addWidget(self.clear_completed_btn)

        self.clear_failed_btn = QPushButton("Clear Failed", self)
        self.clear_failed_btn.clicked.connect(self._clear_failed)
        button_layout.addWidget(self.clear_failed_btn)

        self.close_btn = QPushButton("Close", self)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self._selected_urls_for_retry = []

    def _setup_table(self, table: QTableWidget):
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["URL", "Title", "Format", "Quality", "Date", "Status", "Path/Error"])
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)

    def _load_data(self):
        self._load_completed()
        self._load_failed()

    def _load_completed(self):
        records = self._history.get_completed()
        self._populate_table(self.completed_table, records)

    def _load_failed(self):
        records = self._history.get_failed()
        self._populate_table(self.failed_table, records)
        self.export_failed_btn.setEnabled(len(records) > 0)
        self.retry_failed_btn.setEnabled(len(records) > 0)

    def _populate_table(self, table: QTableWidget, records):
        table.setRowCount(0)

        for idx, record in enumerate(records):
            table.insertRow(idx)

            url_item = QTableWidgetItem(record.url)
            url_item.setToolTip(record.url)
            table.setItem(idx, 0, url_item)

            title_item = QTableWidgetItem(record.title)
            title_item.setToolTip(record.title)
            table.setItem(idx, 1, title_item)

            table.setItem(idx, 2, QTableWidgetItem(record.format))
            table.setItem(idx, 3, QTableWidgetItem(record.quality))

            date_str = self._format_date(record.timestamp)
            table.setItem(idx, 4, QTableWidgetItem(date_str))

            status_item = QTableWidgetItem("Success" if record.success else "Failed")
            table.setItem(idx, 5, status_item)

            if record.success:
                table.setItem(idx, 6, QTableWidgetItem(record.output_path or ""))
            else:
                error_item = QTableWidgetItem(record.error_message)
                error_item.setToolTip(record.error_message)
                table.setItem(idx, 6, error_item)

    def _format_date(self, timestamp: str) -> str:
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return timestamp

    def _on_filter_changed(self):
        filter_text = self.filter_input.text().lower()
        status_filter = self.status_combo.currentText()

        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:
            self._filter_table(self.completed_table, self._history.get_completed(), filter_text, "Completed" if status_filter != "All" else None)
        else:
            self._filter_table(self.failed_table, self._history.get_failed(), filter_text, "Failed" if status_filter != "All" else None)

    def _filter_table(self, table: QTableWidget, records, filter_text: str, status_filter: str = None):
        table.setRowCount(0)

        for idx, record in enumerate(records):
            if status_filter:
                is_completed = record.success
                if status_filter == "Completed" and not is_completed:
                    continue
                if status_filter == "Failed" and is_completed:
                    continue

            text_match = (
                filter_text in record.url.lower() or
                filter_text in record.title.lower() or
                filter_text in record.format.lower() or
                filter_text in record.quality.lower()
            )

            if text_match:
                row_idx = table.rowCount()
                table.insertRow(row_idx)

                url_item = QTableWidgetItem(record.url)
                url_item.setToolTip(record.url)
                table.setItem(row_idx, 0, url_item)

                title_item = QTableWidgetItem(record.title)
                title_item.setToolTip(record.title)
                table.setItem(row_idx, 1, title_item)

                table.setItem(row_idx, 2, QTableWidgetItem(record.format))
                table.setItem(row_idx, 3, QTableWidgetItem(record.quality))

                date_str = self._format_date(record.timestamp)
                table.setItem(row_idx, 4, QTableWidgetItem(date_str))

                status_item = QTableWidgetItem("Success" if record.success else "Failed")
                table.setItem(row_idx, 5, status_item)

                if record.success:
                    table.setItem(row_idx, 6, QTableWidgetItem(record.output_path or ""))
                else:
                    error_item = QTableWidgetItem(record.error_message)
                    error_item.setToolTip(record.error_message)
                    table.setItem(row_idx, 6, error_item)

    def _on_tab_changed(self, index: int):
        self.filter_input.clear()

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

        confirm = QMessageBox.question(
            self,
            "Retry Failed Downloads",
            f"Found {len(failed_urls)} failed URL(s).\n\nAdd them to the download queue?",
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
