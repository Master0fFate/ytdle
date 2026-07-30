import pytest
from PySide6.QtCore import QPoint, QRect, QSettings

import ui.main_window as main_window


@pytest.fixture
def window(qtbot, monkeypatch, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    settings.setValue("directory", str(tmp_path / "downloads"))

    monkeypatch.setattr(main_window, "QSettings", lambda *_args: settings)
    monkeypatch.setattr(main_window, "DownloadHistory", object)
    monkeypatch.setattr(
        main_window,
        "resolve_dependency_paths",
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
    monkeypatch.setattr(
        main_window.MainWindow,
        "_start_dependency_version_probes",
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


def test_queue_cache_never_survives_set_clear_ingest_or_clean(window):
    window.url_input.setPlainText("https://example.com/one")
    assert window._collect_urls() == ["https://example.com/one"]

    window.url_input.setPlainText("https://example.com:bad-port/video")
    assert "Line 1 is malformed" in window._validate_inputs()

    window._clear_urls()
    assert window._collect_urls() == []

    window._add_urls_to_queue(
        ("https://example.com/two\nhttps://example.com/two\ninvalid value",),
        "cache test",
    )
    assert window._collect_urls() == ["https://example.com/two"]

    window.url_input.appendPlainText("https://example.com/two\ninvalid value")
    assert window.clean_urls_button.isEnabled()
    window._clean_url_queue()
    assert window._collect_urls() == ["https://example.com/two"]
    assert not window.clean_urls_button.isEnabled()


def test_queue_cache_reuses_analysis_until_exact_text_changes(window, monkeypatch):
    original = main_window.analyze_url_queue
    calls = []

    def tracked(text):
        calls.append(text)
        return original(text)

    monkeypatch.setattr(main_window, "analyze_url_queue", tracked)
    window.url_input.setPlainText("https://example.com/one")
    assert len(calls) == 1

    assert window._collect_urls() == ["https://example.com/one"]
    assert window._validate_inputs() is None
    window._set_controls_enabled(False)
    window._set_controls_enabled(True)
    assert len(calls) == 1

    window.url_input.setPlainText("https://example.com/two")
    assert window._collect_urls() == ["https://example.com/two"]
    assert len(calls) == 2


def test_compact_layout_uses_one_format_switch_without_overlap(window, qtbot):
    window.resize(760, 600)
    window.show()
    qtbot.wait(20)

    assert window.mp3_btn.parent() is window.format_switch
    assert window.mp4_btn.parent() is window.format_switch
    assert window.mp3_btn.geometry().right() + 1 == window.mp4_btn.geometry().left()

    bounds = QRect(QPoint(0, 0), window.size())
    controls = (
        window.dir_input,
        window.url_input,
        window.format_switch,
        window.quality_combo,
        window.template_presets,
        window.template_line,
        window.ffmpeg_input,
        window.ffmpeg_mode,
        window.history_button,
        window.check_network_button,
        window.start_button,
        window.cancel_button,
        window.pause_button,
        window.skip_button,
    )
    for control in controls:
        top_left = control.mapTo(window, QPoint(0, 0))
        rect = QRect(top_left, control.size())
        assert bounds.contains(rect)

    network_rect = QRect(
        window.check_network_button.mapTo(window, QPoint(0, 0)),
        window.check_network_button.size(),
    )
    start_rect = QRect(
        window.start_button.mapTo(window, QPoint(0, 0)),
        window.start_button.size(),
    )
    assert not network_rect.intersects(start_rect)


def test_settings_writes_are_coalesced_while_typing(window, qtbot):
    timer = window._settings_save_timer
    timer.stop()
    timer.timeout.disconnect()
    saves = []
    timer.timeout.connect(lambda: saves.append(True))

    window.dir_input.setText("C:/Downloads/a")
    window.dir_input.setText("C:/Downloads/ab")
    window.template_line.setText("%(title)s")

    assert timer.isActive()
    qtbot.waitUntil(lambda: len(saves) == 1, timeout=750)
    assert saves == [True]


def test_statuses_render_in_console_and_live_updates_replace_the_last_line(window):
    assert window.status_label.isHidden()
    assert window.dependency_label.isHidden()
    assert window.network_label.isHidden()
    assert "Status: Ready" in window.log_output.toPlainText()

    window._on_status("Downloading at 1 MiB/s")
    live_block_count = window.log_output.document().blockCount()
    window._on_status("Downloading at 2 MiB/s")

    assert window.log_output.document().blockCount() == live_block_count
    assert window.log_output.document().lastBlock().text() == (
        "Status: Downloading at 2 MiB/s"
    )

    window._on_error("Download failed")
    assert window.log_output.document().lastBlock().text() == (
        "Status: Download failed"
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
