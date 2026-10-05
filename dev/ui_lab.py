"""Dev-only UI lab: flip YTDLE between demo data and realistic worst cases.

    python -m dev.ui_lab                 # opens with Demo data
    python -m dev.ui_lab --data worst    # demo | worst | empty | one | huge
    python -m dev.ui_lab --shots DIR     # screenshot every state, page, and size
    python -m dev.ui_lab --skin angelcore  # default | material3 | angelcore (also with --shots)

The window is the real MainWindow. Fixtures enter only through its data
boundaries (saved settings, detected tools, history store, link editor, and
the worker's signals), never by editing widgets. Not imported by the app or
packaged in release builds.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QButtonGroup, QFrame, QHBoxLayout, QPushButton

import ui.main_window as main_window
from dev.ui_fixtures import STATE_LABELS, STATES, Fixture, build
from ui.components.history_dialog import HistoryDialog
from ui.skins import SKINS
from ui.styles import apply_chrome

_SETTINGS_DIR = Path(tempfile.gettempdir()) / "ytdle-ui-lab"


class FixtureHistory:
    """History store shaped like core.history.DownloadHistory, backed by a list."""

    def __init__(self, records):
        self._records = list(records)

    def get_all(self, limit=None):
        return self._records[:limit] if limit else list(self._records)

    def get_completed(self, limit=None):
        return [r for r in self._records if r.success][:limit]

    def get_failed(self, limit=None):
        return [r for r in self._records if not r.success][:limit]

    def get_failed_urls(self):
        return list(dict.fromkeys(r.url for r in self._records if not r.success))

    def export_failed(self, _path):
        return True

    def clear_completed(self):
        self._records = [r for r in self._records if not r.success]

    def clear_failed(self):
        self._records = [r for r in self._records if r.success]

    def close(self):
        pass


class _Probe:
    """Stands in for the network socket so the online/offline result is fixed."""

    def abort(self):
        pass

    def deleteLater(self):
        pass


def open_window(fixture: Fixture, skin: str = "default") -> main_window.MainWindow:
    _SETTINGS_DIR.mkdir(exist_ok=True)
    path = _SETTINGS_DIR / "settings.ini"
    path.unlink(missing_ok=True)
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    for key, value in fixture.settings.items():
        settings.setValue(key, value)
    # The skin arrives the way a user's choice does: from saved settings.
    settings.setValue("skin", skin)

    main_window.QSettings = lambda *_args: settings
    main_window.resolve_dependency_paths = lambda: dict(fixture.tools)
    main_window.DownloadHistory = lambda: FixtureHistory(fixture.history)
    main_window.MainWindow._check_network_status = lambda _self: None
    main_window.MainWindow._start_dependency_version_probes = lambda _self: None

    window = main_window.MainWindow()
    # Same fallback as main.py.
    if not window.dir_input.text().strip():
        window.dir_input.setText(window._default_download_dir())
    probe = _Probe()
    window._network_socket = probe
    window._finish_network_check(probe, fixture.online)

    window.url_input.setPlainText(fixture.links)
    if fixture.events or fixture.finished:
        urls = window._collect_urls()
        window._set_controls_enabled(False)
        window.session_list.start_session(urls)
        window._downloading_total = len(urls)
        handlers = {
            "started": lambda e: window._on_item_started(e.url),
            "finished": lambda e: window._on_item_finished(e.url, e.ok, e.info),
            "status": lambda e: window._on_status(e.info),
            "progress": lambda e: window._on_progress(e.value),
        }
        for event in fixture.events:
            handlers[event.kind](event)
        if fixture.finished:
            window._on_all_finished(*fixture.finished)
    return window


class Toggle(QFrame):
    """Plain dev chrome: a gray track with a white pill on the active state."""

    def __init__(self, on_change, current: str):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(
            "QFrame { background: #d4d4d8; border-radius: 16px; }"
            "QPushButton { background: transparent; color: #18181b; border: none; border-radius: 13px;"
            " padding: 5px 12px; font: 9pt 'Segoe UI'; min-height: 0; }"
            "QPushButton:checked { background: #ffffff; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.group = QButtonGroup(self)
        for state in STATES:
            button = QPushButton(STATE_LABELS[state], self)
            button.setCheckable(True)
            button.setChecked(state == current)
            self.group.addButton(button)
            layout.addWidget(button)
            button.clicked.connect(lambda _checked=False, s=state: on_change(s))


def interactive(state: str, skin: str) -> int:
    app = QApplication(sys.argv)
    apply_chrome(app, skin)
    holder: dict = {}

    def show(new_state: str) -> None:
        old = holder.get("window")
        geometry = old.geometry() if old else None
        window = open_window(build(new_state), skin)
        if geometry is not None:
            window.setGeometry(geometry)
        window.show()
        if old is not None:
            old.close()
        holder["window"] = window
        toggle = holder["toggle"]
        toggle.adjustSize()
        screen = app.primaryScreen().availableGeometry()
        toggle.move(screen.center().x() - toggle.width() // 2, screen.bottom() - toggle.height() - 16)
        toggle.raise_()

    holder["toggle"] = Toggle(show, state)
    holder["toggle"].show()
    show(state)
    return app.exec()


def screenshots(target: Path, skins: list[str]) -> int:
    app = QApplication(sys.argv)
    target.mkdir(parents=True, exist_ok=True)
    for skin in skins:
        apply_chrome(app, skin)
        _screenshots_for(app, target / skin, skin)
    return 0


def _screenshots_for(app, target: Path, skin: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    sizes = ((760, 560), (920, 640), (2560, 1440))
    for state in STATES:
        started = time.perf_counter()
        fixture = build(state)
        window = open_window(fixture, skin)
        built = time.perf_counter() - started
        window.show()
        for width, height in sizes:
            window.resize(width, height)
            for page, name in enumerate(("download", "options", "cookies")):
                window._show_page(page)
                app.processEvents()
                window.grab().save(str(target / f"{state}-{width}-{name}.png"))
            window._show_page(0)
            window.activity_log_button.click()
            app.processEvents()
            window.grab().save(str(target / f"{state}-{width}-log.png"))
            window.activity_items_button.click()
        started = time.perf_counter()
        dialog = HistoryDialog(window._history, window)
        opened = time.perf_counter() - started
        dialog.resize(900, 600)
        dialog.show()
        app.processEvents()
        dialog.grab().save(str(target / f"{state}-history.png"))
        dialog.tab_widget.setCurrentIndex(1)
        app.processEvents()
        dialog.grab().save(str(target / f"{state}-history-failed.png"))
        print(f"{state}: window {built * 1000:.0f} ms, history dialog {opened * 1000:.0f} ms")
        dialog.close()
        window.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", choices=STATES, default=os.environ.get("YTDLE_UI_DATA", "demo"))
    parser.add_argument("--skin", choices=[*SKINS, "all"], default="default")
    parser.add_argument("--shots", type=Path, help="write screenshots of every state to this folder and exit")
    args = parser.parse_args()
    if args.shots:
        return screenshots(args.shots, list(SKINS) if args.skin == "all" else [args.skin])
    return interactive(args.data, "default" if args.skin == "all" else args.skin)


if __name__ == "__main__":
    sys.exit(main())
