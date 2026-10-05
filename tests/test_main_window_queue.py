from collections import Counter

import pytest
from PySide6.QtCore import QPoint, QRect, QSettings
from PySide6.QtWidgets import QApplication

from ui.styles import apply_chrome

import ui.main_window as main_window
from ui.components.session_list import SessionList


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
    assert window.queue_label.text().startswith("2 links")
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


def _rect(window, widget):
    return QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())


@pytest.mark.parametrize("size", [(760, 560), (920, 640)])
def test_layout_reads_top_to_bottom_without_overlap(window, qtbot, size):
    apply_chrome(QApplication.instance())
    window.resize(*size)
    window.show()
    qtbot.wait(20)

    for button in (window.title_bar.min_btn, window.title_bar.close_btn):
        assert window.title_bar.rect().contains(button.geometry())
        assert button.geometry().top() >= 4
        assert window.title_bar.height() - button.geometry().bottom() >= 4

    assert window.mp3_btn.parent() is window.format_switch
    assert window.mp4_btn.parent() is window.format_switch
    assert window.mp3_btn.geometry().right() + 1 == window.mp4_btn.geometry().left()

    bounds = QRect(QPoint(0, 0), window.size())
    # Links, then what to download, then where, then the action, then activity.
    rows = (
        window.drop_zone,
        window.format_switch,
        window.dir_input,
        window.start_button,
        window.progress_bar,
        window.session_list,
    )
    others = (
        window.quality_combo,
        window.playlist_checkbox,
        window.browse_button,
        window.open_folder_button,
        window.paste_button,
        window.history_button,
        window.check_network_button,
        window.network_label,
    )
    for control in rows + others:
        assert control.isVisible()
        assert bounds.contains(_rect(window, control))
    for upper, lower in zip(rows, rows[1:]):
        assert _rect(window, upper).bottom() < _rect(window, lower).top()

    last_nav = window.nav_group.button(len(main_window._PAGES) - 1)
    assert _rect(window, last_nav).right() < _rect(window, window.network_label).left()
    assert window.start_button.width() >= 120


def test_running_batch_swaps_download_for_transport(window):
    transport = (window.cancel_button, window.pause_button, window.skip_button)
    assert not window.start_button.isHidden()
    assert all(button.isHidden() for button in transport)

    window._set_controls_enabled(False)
    assert window.start_button.isHidden()
    assert all(not button.isHidden() and button.isEnabled() for button in transport)
    assert not window.url_input.isEnabled()

    window._set_controls_enabled(True)
    assert not window.start_button.isHidden()
    assert all(button.isHidden() for button in transport)


def test_actions_are_named_and_discoverable(window):
    for button in (
        window.import_urls_button, window.clean_urls_button, window.clear_urls_button,
        window.history_button, window.check_network_button,
        window.pause_button, window.skip_button,
    ):
        assert not button.text()
        assert not button.icon().isNull()
        assert button.accessibleName()
        assert button.toolTip()
    for button in (window.start_button, window.cancel_button, window.paste_button):
        assert button.text()
        assert button.accessibleName()
        assert button.toolTip()
    assert window.mp3_btn.text() == "MP3"
    assert window.mp4_btn.text() == "MP4"
    assert window.cookie_file_browse.accessibleName() == "Browse for cookie file"


def test_download_button_counts_links_and_plan_is_visible(window):
    assert window.start_button.text() == "Download"
    assert not window.empty_state.isHidden()
    assert window.status_detail.text().startswith("Add links to start · MP3")

    window.url_input.setPlainText("https://example.com/a\nhttps://example.com/b")

    assert window.start_button.text() == "Download 2"
    assert window.empty_state.isHidden()
    assert window.status_detail.text().startswith("2 links · MP3 320k · to ")


def test_invalid_start_explains_inline_without_a_dialog(window, monkeypatch):
    monkeypatch.setattr(
        main_window.QMessageBox,
        "warning",
        lambda *_args: pytest.fail("validation must not open a modal dialog"),
    )
    window.url_input.setPlainText("https://example.com/a\nnot a link")

    window._start_downloads()

    assert window.status_label.text() == "Line 2 contains spaces."
    assert window.status_label.property("state") == "error"
    assert "Clean Queue" in window.status_detail.text()
    assert window._controls_enabled


def test_paste_button_merges_clipboard_links(window):
    QApplication.clipboard().setText("https://example.com/a\nhttps://example.com/a")
    window._paste_from_clipboard()
    assert window._collect_urls() == ["https://example.com/a"]
    assert window.status_label.text() == (
        "Added 1 link from the clipboard. Skipped 1 duplicate."
    )


def test_batch_progress_is_monotonic_and_rows_track_each_link(window, qtbot):
    urls = ["https://example.com/a", "https://example.com/b"]
    window.session_list.start_session(urls)
    window._set_controls_enabled(False)
    window._downloading_total = 2

    window._on_item_started(urls[0])
    assert window.status_label.text() == "Downloading · 0 of 2 finished"
    window._on_progress(80)
    # Concurrent items report their own percentages; the batch bar never goes back.
    window._on_progress(10)
    assert window._progress_floor == 40
    assert window.windowTitle() == "40% · YTDLE"

    window._on_item_finished(urls[0], True, "C:/Downloads/a.mp3")
    window._on_item_started(urls[1])
    window._on_item_finished(urls[1], False, "ERROR: [site] b: Private video")
    window._on_all_finished(1, 1)

    assert window.session_list.counts() == Counter(done=1, failed=1)
    assert SessionList.item_detail(window.session_list.item(0)) == "C:/Downloads/a.mp3"
    assert SessionList.item_detail(window.session_list.item(1)) == "[site] b: Private video"
    assert window.status_label.text() == "1 saved, 1 failed"
    assert window._controls_enabled
    assert window.windowTitle() == "YTDLE"
    qtbot.waitUntil(lambda: window.progress_bar.value() == 100, timeout=1000)


def test_cancelled_batch_marks_unstarted_rows(window):
    urls = ["https://example.com/a", "https://example.com/b"]
    window.session_list.start_session(urls)
    window._set_controls_enabled(False)
    window._downloading_total = 2
    window._on_item_started(urls[0])
    window._on_item_finished(urls[0], False, "Cancelled")
    window._on_all_finished(0, 0)

    assert window.session_list.counts() == Counter(stopped=2)
    assert window.status_label.text() == "Stopped. Nothing was saved."


def test_activity_view_is_bounded_while_persistent_log_is_unchanged(window):
    for index in range(1600):
        window.append_log(f"Entry {index}")
    assert window.log_output.document().blockCount() == 1500
    assert "Entry 0" not in window.log_output.toPlainText()
    assert "Entry 1599" in window.log_output.toPlainText()


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
    assert not window.status_label.isHidden()
    assert window.status_label.text() == "Ready"
    assert window.network_label.text() == "Checking…"
    assert "Status: Ready" in window.log_output.toPlainText()

    window._on_status("Downloading at 1 MiB/s")
    live_block_count = window.log_output.document().blockCount()
    window._on_status("Downloading at 2 MiB/s")

    assert window.log_output.document().blockCount() == live_block_count
    assert window.log_output.document().lastBlock().text() == (
        "Status: Downloading at 2 MiB/s"
    )
    assert window.status_detail.text() == "Downloading at 2 MiB/s"

    window._on_error("Download failed")
    assert window.log_output.document().lastBlock().text() == (
        "Status: Download failed"
    )
    assert window.status_label.property("state") == "error"


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
