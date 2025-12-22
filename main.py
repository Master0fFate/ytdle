import argparse
import ctypes
import sys
import os
from typing import List

from core.logger import setup_logging
from core.config import DownloadOptions
from core.downloader import DownloadManager


class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False
    @property
    def encoding(self):
        return "utf-8"


def hide_console_window():
    """
    Hides the console window if it exists.
    Used when running in GUI mode from a console-subsystem executable.
    """
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE
    except Exception:
        pass


def run_cli(args) -> None:
    print("YTDLE CLI Mode")
    print("-" * 30)

    urls = [u.strip() for u in args.input if u.strip()]
    if not urls:
        print("Error: No valid URLs provided.")
        sys.exit(1)

    directory = os.path.abspath(args.output_dir)
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        sys.exit(1)

    is_mp3 = (args.format.lower() == 'mp3')
    
    quality = args.quality
    if not quality:
        quality = "192k" if is_mp3 else "Best"

    opts = DownloadOptions(
        is_mp3=is_mp3,
        quality=quality,
        outtmpl_template=args.template,
        directory=directory,
        download_playlist=args.playlist,
        restrict_filenames=args.restrict,
        nocheckcertificate=args.no_check_certificate,
        cookies=args.cookies,
        ffmpeg_add_args=args.ffmpeg_add_args,
        ffmpeg_override_args=args.ffmpeg_override_args
    )

    print(f"URLs: {len(urls)}")
    print(f"Directory: {directory}")
    print(f"Format: {args.format.upper()} ({quality})")
    print(f"Playlist: {args.playlist}")
    print("-" * 30)

    def on_progress(pct: int):

        bar_len = 30
        filled = int(pct * bar_len / 100)
        bar = '=' * filled + '-' * (bar_len - filled)
        msg = f"\r[{bar}] {pct}%"
        try:
            sys.stdout.write(msg)
            sys.stdout.flush()
        except:
            pass

    def on_status(msg: str):
        if "Downloading..." in msg:
             try:
                sys.stdout.write(f" | {msg}")
                sys.stdout.flush()
             except:
                pass
        else:
             print(f"\nStatus: {msg}")

    def on_log(msg: str):
        if args.verbose:
            print(f"\nLog: {msg}")

    def on_error(msg: str):
        print(f"\nERROR: {msg}")

    def on_item_started(url: str):
        print(f"\n\n[Item] {url}")

    def on_item_finished(url: str, success: bool, info: str):
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
        print(f"Info: {info}")

    def on_all_finished(success: int, fail: int):
        print("\n" + "=" * 30)
        print(f"Batch Complete. Success: {success}, Failed: {fail}")
        sys.exit(1 if fail > 0 else 0)

    manager = DownloadManager(
        urls=urls,
        options=opts,
        on_progress=on_progress,
        on_status=on_status,
        on_log=on_log,
        on_error=on_error,
        on_item_started=on_item_started,
        on_item_finished=on_item_finished,
        on_all_finished=on_all_finished
    )

    try:
        manager.run()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        manager.cancel()
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="YTDLE Media Downloader")
    parser.add_argument("-i", "--input", nargs="+", help="Input URL(s)")
    parser.add_argument("-od", "--output-dir", default=os.getcwd(), help="Output directory (default: current)")
    parser.add_argument("-f", "--format", choices=["mp3", "mp4"], default="mp3", help="Download format (default: mp3)")
    parser.add_argument("-q", "--quality", help="Quality (e.g., 192k, 1080p, Best)")
    parser.add_argument("-p", "--playlist", action="store_true", help="Download playlist")
    parser.add_argument("-r", "--restrict", action="store_true", help="Restrict filenames to ASCII")
    parser.add_argument("-t", "--template", default="%(title).150s", help="Output filename template")
    parser.add_argument("--no-check-certificate", action="store_true", help="Disable SSL certificate validation")
    parser.add_argument("--cookies", help="Path to cookies file (for authentication/anti-bot)")
    parser.add_argument("--ffmpeg-add-args", help="Append extra args for ffmpeg (e.g. '-vcodec libx264')")
    parser.add_argument("--ffmpeg-override-args", help="Override args for ffmpeg (may replace default post-processor configs)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # If len(sys.argv) == 1, run GUI.
    
    if len(sys.argv) == 1:
        # GUI MODE
        if sys.platform == "win32":
            hide_console_window()

        from PySide6.QtWidgets import QApplication
        from ui.styles import STYLESHEET
        from ui.main_window import MainWindow

        setup_logging(verbose=False)
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLESHEET)
        win = MainWindow()
        if not win.dir_input.text().strip():
            win.dir_input.setText(win._default_download_dir())
        win.show()
        sys.exit(app.exec())
    else:
        # CLI MODE
        args = parser.parse_args()
        setup_logging(verbose=args.verbose)
        run_cli(args)


if __name__ == "__main__":
    main()
