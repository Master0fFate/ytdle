import pytest
from PySide6.QtCore import QSettings

import ui.main_window as main_window


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    settings.setValue("directory", str(tmp_path / "downloads"))

    monkeypatch.setattr(main_window, "QSettings", lambda *_args: settings)
    monkeypatch.setattr(main_window, "DownloadHistory", object)
    monkeypatch.setattr(
        main_window,
        "check_dependencies",
        lambda: {
            "ffmpeg": "C:/Tools/ffmpeg.exe",
            "aria2c": "C:/Tools/aria2c.exe",
            "yt_dlp": "test-version",
            "ffmpeg_version": "test-version",
            "aria2c_version": "test-version",
        },
    )
    monkeypatch.setattr(
        main_window.MainWindow,
        "_check_network_status",
        lambda _self: None,
    )

    widget = main_window.MainWindow()
    widget.dir_input.setText(str(tmp_path / "downloads"))
    qtbot.addWidget(widget)
    return widget


def test_main_window_queue_validation_and_cleaning(window):
    window.url_input.setPlainText(
        "https://example.com/one\n"
        "https://example.com/one\n"
        "not a link\n"
        "https://example.com/two"
    )

    assert window._collect_urls() == [
        "https://example.com/one",
        "https://example.com/two",
    ]
    assert "Queue: 2 links" in window.queue_label.text()
    assert "1 duplicate" in window.queue_label.text()
    assert "1 invalid" in window.queue_label.text()
    assert "Line 3 contains spaces" in window._validate_inputs()
    assert window.clean_urls_button.isEnabled()

    window._clean_url_queue()

    assert window.url_input.toPlainText() == (
        "https://example.com/one\nhttps://example.com/two"
    )
    assert window._validate_inputs() is None
    assert not window.clean_urls_button.isEnabled()


def test_main_window_ingestion_uses_real_newlines_and_skips_duplicates(window):
    window.url_input.setPlainText("https://example.com/one")

    result = window._add_urls_to_queue(
        ("https://example.com/one\nhttps://example.com/two\ninvalid entry",),
        "test list",
    )

    assert result.added_urls == ("https://example.com/two",)
    assert window.url_input.toPlainText() == (
        "https://example.com/one\nhttps://example.com/two"
    )
    assert "\\n" not in window.url_input.toPlainText()
    assert window.status_label.text() == (
        "Added 1 link from test list. Skipped 1 duplicate and 1 invalid entry."
    )


def test_import_url_list_reads_utf8_and_uses_queue_ingestion(
    window,
    monkeypatch,
    tmp_path,
):
    url_list = tmp_path / "batch.txt"
    url_list.write_text(
        "# Exported list\n"
        "https://example.com/one\n"
        "https://example.com/one\n"
        "https://example.com/two",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        main_window.QFileDialog,
        "getOpenFileName",
        lambda *_args: (str(url_list), ""),
    )

    window._import_url_list()

    assert window.url_input.toPlainText() == (
        "https://example.com/one\nhttps://example.com/two"
    )
    assert window.status_label.text() == (
        "Added 2 links from batch.txt. Skipped 1 duplicate."
    )


def test_import_url_list_reports_non_utf8_input(window, monkeypatch, tmp_path):
    url_list = tmp_path / "legacy.txt"
    url_list.write_bytes(b"\xff\xfe\x00")
    warnings = []
    monkeypatch.setattr(
        main_window.QFileDialog,
        "getOpenFileName",
        lambda *_args: (str(url_list), ""),
    )
    monkeypatch.setattr(
        main_window.QMessageBox,
        "warning",
        lambda _parent, title, message: warnings.append((title, message)),
    )

    window._import_url_list()

    assert window.url_input.toPlainText() == ""
    assert warnings == [
        (
            "Cannot Read List",
            "YTDLE could not read legacy.txt. Save it as UTF-8 text and try again.",
        )
    ]
