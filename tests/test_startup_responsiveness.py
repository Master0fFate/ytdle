from PySide6.QtCore import QObject, QSettings, Signal

import ui.main_window as main_window


class FakeHistory:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeSocket(QObject):
    connected = Signal()
    errorOccurred = Signal(object)
    instances = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aborted = False
        self.target = None
        type(self).instances.append(self)

    def connectToHost(self, host, port):
        self.target = (host, port)

    def abort(self):
        self.aborted = True


def test_network_probe_is_repeatable_nonblocking_and_cancelled_on_close(
    qtbot, monkeypatch, tmp_path
):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    settings.setValue("directory", str(tmp_path / "downloads"))
    history = FakeHistory()
    FakeSocket.instances = []

    monkeypatch.setattr(main_window, "QSettings", lambda *_args: settings)
    monkeypatch.setattr(main_window, "DownloadHistory", lambda: history)
    monkeypatch.setattr(main_window, "QTcpSocket", FakeSocket)
    monkeypatch.setattr(
        main_window,
        "resolve_dependency_paths",
        lambda: {
            "ffmpeg": "C:/Tools/ffmpeg.exe",
            "aria2c": "C:/Tools/aria2c.exe",
            "yt_dlp": "test-version",
            "ffmpeg_version": "unknown",
            "aria2c_version": "unknown",
        },
    )
    monkeypatch.setattr(
        main_window.MainWindow,
        "_start_dependency_version_probes",
        lambda _self: None,
    )

    window = main_window.MainWindow()
    qtbot.addWidget(window)
    first = FakeSocket.instances[-1]
    assert first.target == ("8.8.8.8", 53)
    assert window.network_label.text() == "Network: Checking..."
    assert not window.check_network_button.isEnabled()
    console = window.log_output.toPlainText()
    assert "Toolchain: FFmpeg ready" in console
    assert "Ready" in console
    assert "Network status: Checking..." in console

    window._check_network_status()
    second = FakeSocket.instances[-1]
    assert first.aborted
    assert second is not first
    first.connected.emit()
    assert window.network_label.text() == "Network: Checking..."

    second.connected.emit()
    assert window.network_label.text() == "Network: Online | yt-dlp: test-version"
    assert "Network status: Online" in window.log_output.toPlainText()
    assert window.check_network_button.isEnabled()

    window._set_controls_enabled(False)
    window._check_network_status()
    third = FakeSocket.instances[-1]
    third.errorOccurred.emit(object())
    assert window.network_label.text() == "Network: Offline | yt-dlp: test-version"
    assert not window.check_network_button.isEnabled()

    window._set_controls_enabled(True)
    assert window.check_network_button.isEnabled()
    window._check_network_status()
    pending = FakeSocket.instances[-1]
    window.close()

    assert pending.aborted
    assert not window._network_timer.isActive()
    assert history.closed
