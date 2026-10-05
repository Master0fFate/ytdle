import re

import pytest
from PySide6.QtCore import QPoint, QRect, QSettings
from PySide6.QtWidgets import QApplication

import ui.main_window as main_window
from ui.components.toggle_switch import ToggleSwitch
from ui.skins import COLORS, DEFAULT_SKIN, SKINS, active_skin, resolve
from ui.styles import apply_chrome


@pytest.fixture
def make_window(qtbot, monkeypatch, tmp_path):
    def _make(skin=None):
        settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
        settings.setValue("directory", str(tmp_path / "downloads"))
        if skin:
            settings.setValue("skin", skin)
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
        monkeypatch.setattr(main_window.MainWindow, "_check_network_status", lambda _self: None)
        monkeypatch.setattr(
            main_window.MainWindow, "_start_dependency_version_probes", lambda _self: None
        )
        window = main_window.MainWindow()
        qtbot.addWidget(window)
        return window, settings

    return _make


def test_unknown_or_missing_skin_falls_back_to_default():
    assert resolve("neon").key == DEFAULT_SKIN
    assert resolve(None).key == DEFAULT_SKIN
    assert list(SKINS) == ["default", "material3", "angelcore"]


def test_picking_a_skin_applies_live_and_is_saved(make_window):
    window, settings = make_window()
    assert active_skin().key == "default"
    assert window.start_button.text() == "Download"
    assert not window.import_urls_button.icon().isNull()

    window.skin_group.button(window._skin_keys.index("angelcore")).click()

    assert active_skin().key == "angelcore"
    assert settings.value("skin") == "angelcore"
    assert COLORS["bg"] == "#090909"
    # Words instead of icons, marks instead of colored dots.
    assert window.start_button.text() == "[download]"
    assert window.import_urls_button.text() == "[import]"
    assert window.import_urls_button.icon().isNull()
    assert window.browse_button.text() == "[browse]"
    assert window.status_dot.isHidden()
    assert window.network_label.text() == "[checking]"
    assert window.nav_group.button(0).text() == "> Download"
    assert window.mp3_btn.text() == "MP3"
    # Accessible names never change with the look.
    assert window.import_urls_button.accessibleName() == "Import URL list"

    window._on_error("Download failed")
    assert window.status_label.text() == "[!] Download failed"

    window.skin_group.button(window._skin_keys.index("material3")).click()
    assert settings.value("skin") == "material3"
    assert window.start_button.text() == "Download"
    assert not window.import_urls_button.icon().isNull()
    assert window.status_label.text() == "Download failed"
    assert not window.status_dot.isHidden()
    assert window.nav_group.button(0).text() == "Download"


def test_saved_skin_is_restored_on_start(make_window):
    window, _settings = make_window(skin="angelcore")
    assert active_skin().key == "angelcore"
    assert window.skin_group.checkedButton().text() == "Angelcore"
    assert window.skin_summary.text() == SKINS["angelcore"].summary


@pytest.mark.parametrize("skin", list(SKINS))
@pytest.mark.parametrize("size", [(760, 480), (760, 560), (920, 640)])
def test_every_skin_keeps_the_layout_readable(make_window, qtbot, skin, size):
    window, _settings = make_window()
    apply_chrome(QApplication.instance(), skin)
    window._apply_skin_presentation()
    # The floor height is what small or high-DPI screens get.
    window.setMinimumSize(main_window._MIN_WIDTH, main_window._FLOOR_HEIGHT)
    window.resize(*size)
    window.show()
    qtbot.wait(20)

    def rect(widget):
        return QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())

    bounds = QRect(QPoint(0, 0), window.size())
    rows = (
        window.drop_zone,
        window.format_switch,
        window.dir_input,
        window.start_button,
        window.progress_bar,
        window.session_list,
    )
    for control in rows + (window.network_label, window.history_button, window.paste_button):
        assert control.isVisible()
        assert bounds.contains(rect(control)), control.objectName()
    for upper, lower in zip(rows, rows[1:]):
        assert rect(upper).bottom() < rect(lower).top()
    last_nav = window.nav_group.button(len(main_window._PAGES) - 1)
    assert rect(last_nav).right() < rect(window.network_label).left()


def test_switch_style_follows_the_skin(qtbot):
    switch = ToggleSwitch("Whole playlist")
    qtbot.addWidget(switch)

    def lead() -> int:
        # Width before the label: the track, or the [x] mark.
        text = switch.fontMetrics().horizontalAdvance(switch.text())
        return switch.sizeHint().width() - text - switch.TEXT_GAP - 4

    apply_chrome(QApplication.instance(), "angelcore")
    assert lead() == switch.fontMetrics().horizontalAdvance("[x]")
    apply_chrome(QApplication.instance(), "material3")
    assert lead() == 52  # Material 3 switch track
    assert switch.sizeHint().height() == 32
    apply_chrome(QApplication.instance(), "default")
    assert lead() == int(switch.TRACK_WIDTH)


def test_angelcore_passes_its_release_gate():
    skin = SKINS["angelcore"]
    sheet = skin.stylesheet(skin.colors, "")
    # Square geometry everywhere, no gradients, neutral inks only.
    radii = re.findall(r"border-radius:\s*([^;]+);", sheet)
    assert radii and all(value.strip() in ("0", "0px") for value in radii)
    assert "gradient" not in sheet
    for value in list(skin.colors.values()) + re.findall(r"#[0-9a-fA-F]{6}", sheet):
        red, green, blue = (int(value[i : i + 2], 16) for i in (1, 3, 5))
        assert red == green == blue, value
    # No resting box: the light control ink is never a border color.
    assert f"border: 1px solid {skin.colors['outline']}" not in sheet.split("[state=\"drag\"]")[0]


def test_material3_uses_spec_shapes():
    skin = SKINS["material3"]
    sheet = skin.stylesheet(skin.colors, "")
    assert "border-top-left-radius: 4px" in sheet  # filled text field
    assert "border-bottom: 3px solid" in sheet  # tab indicator
    assert skin.colors["on_accent"] == "#381e72"
