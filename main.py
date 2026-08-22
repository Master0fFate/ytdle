import ctypes
import sys

from core.cli import run_cli
from core.logger import setup_logging


def hide_console_window() -> None:
    """Hide the console window when the GUI is started from YTDLE.exe."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except (AttributeError, OSError):
        return


def main() -> None:
    # No arguments keep the established desktop-app behavior. Every argument
    # selects the terminal interface implemented in core.cli.
    if len(sys.argv) == 1:
        if sys.platform == "win32":
            hide_console_window()

        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.styles import STYLESHEET

        setup_logging(verbose=False)
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLESHEET)
        window = MainWindow()
        if not window.dir_input.text().strip():
            window.dir_input.setText(window._default_download_dir())
        window.show()
        sys.exit(app.exec())

    sys.exit(run_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
