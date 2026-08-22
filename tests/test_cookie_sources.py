import pytest
from PySide6.QtCore import QSettings

import ui.main_window as main_window


@pytest.fixture
def make_window(qtbot, monkeypatch, tmp_path):
    """Factory so tests can seed settings before the window loads them."""

    def _make(settings=None):
        if settings is None:
            settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
        if not settings.contains("directory"):
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

    return _make


@pytest.fixture
def window(make_window):
    return make_window()


def test_cookie_file_source_is_exclusive(window, tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")

    window.browser_combo.setCurrentText("Cookie File (Fallback)")
    window.cookie_file_input.setText(str(cookie_file))

    from_browser, cookies, logs = window._collect_cookie_settings()

    assert from_browser is None
    assert cookies == str(cookie_file)
    assert any("file" in line and "exclusive" in line for line in logs)


def test_browser_source_ignores_cookie_file(window, tmp_path):
    window.browser_combo.setCurrentText("chrome")
    window.cookie_file_input.setText(str(tmp_path / "cookies.txt"))

    from_browser, cookies, logs = window._collect_cookie_settings()

    assert from_browser == ("chrome", None, None, None)
    assert cookies is None
    assert any("ignored" in line for line in logs)


def test_fallback_without_file_warns(window):
    window.browser_combo.setCurrentText("Cookie File (Fallback)")
    window.cookie_file_input.setText("")

    from_browser, cookies, logs = window._collect_cookie_settings()

    assert from_browser is None
    assert cookies is None
    assert any("Warning" in line and "no cookie" in line for line in logs)


def test_fallback_with_missing_file_warns_but_sends_path(window, tmp_path):
    window.browser_combo.setCurrentText("Cookie File (Fallback)")
    window.cookie_file_input.setText(str(tmp_path / "missing.txt"))

    from_browser, cookies, logs = window._collect_cookie_settings()

    assert from_browser is None
    assert cookies == str(tmp_path / "missing.txt")
    assert any("not found" in line for line in logs)


def test_none_sends_no_cookies_even_with_file_set(window, tmp_path):
    window.browser_combo.setCurrentText("None")
    window.cookie_file_input.setText(str(tmp_path / "cookies.txt"))

    from_browser, cookies, logs = window._collect_cookie_settings()

    assert from_browser is None
    assert cookies is None
    assert any("Cookies: none" in line for line in logs)


def test_legacy_config_migrates_to_cookie_file_source(make_window, tmp_path):
    settings = QSettings(str(tmp_path / "legacy.ini"), QSettings.IniFormat)
    settings.setValue("cookie_browser", "None")
    settings.setValue("cookie_file", "C:/cookies/exported.txt")

    widget = make_window(settings)

    assert widget.browser_combo.currentText() == "Cookie File (Fallback)"
    assert widget.cookie_file_input.text() == "C:/cookies/exported.txt"


def test_saved_browser_source_is_restored(make_window, tmp_path):
    settings = QSettings(str(tmp_path / "browser.ini"), QSettings.IniFormat)
    settings.setValue("cookie_browser", "firefox")
    settings.setValue("cookie_profile", "Personal")
    settings.setValue("cookie_file", "C:/cookies/ignored.txt")

    widget = make_window(settings)

    assert widget.browser_combo.currentText() == "firefox"
    assert widget.profile_input.isEnabled()


def test_browse_auto_selects_fallback_from_none(window, monkeypatch, tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    monkeypatch.setattr(
        main_window.QFileDialog,
        "getOpenFileName",
        lambda *_args: (str(cookie_file), ""),
    )

    assert window.browser_combo.currentText() == "None"
    window._choose_cookie_file()

    assert window.browser_combo.currentText() == "Cookie File (Fallback)"
    assert window.cookie_file_input.text() == str(cookie_file)


def test_browser_fields_disabled_for_non_browser_sources(window):
    window.browser_combo.setCurrentText("Cookie File (Fallback)")
    assert not window.profile_input.isEnabled()
    assert not window.keyring_input.isEnabled()
    assert not window.container_input.isEnabled()

    window.browser_combo.setCurrentText("None")
    assert not window.profile_input.isEnabled()

    window.browser_combo.setCurrentText("chrome")
    assert window.profile_input.isEnabled()
    assert window.keyring_input.isEnabled()
    assert window.container_input.isEnabled()
