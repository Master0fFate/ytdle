#!/usr/bin/env python3
"""
Build script for YTDLE release with full metadata.
"""

from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import List

VERSION = "2.1.0"
AUTHOR = "Master0fFate"
DESCRIPTION = "YTDLE Media Downloader - Modern GUI/CLI downloader built with Python and PySide6"
APP_NAME = "YTDLE"
ROOT_DIR = Path(__file__).resolve().parent
VERSION_FILE = ROOT_DIR / "version_info.txt"
ENTRY_POINT = ROOT_DIR / "main.py"


def _python_file_version(version: str) -> str:
    """Convert semver-like strings to a 4-part Windows file version tuple."""
    parts = [p for p in version.split(".") if p.strip().isdigit()]
    nums = [int(p) for p in parts[:4]]
    while len(nums) < 4:
        nums.append(0)
    return ", ".join(str(n) for n in nums)


def _get_pyinstaller_command() -> List[str]:
    """Prefer pyinstaller on PATH, fall back to python -m PyInstaller."""
    if shutil.which("pyinstaller"):
        return ["pyinstaller"]
    return [sys.executable, "-m", "PyInstaller"]


def _clean_build_artifacts() -> None:
    """Remove previous build outputs without touching user-maintained spec files."""
    for folder in (ROOT_DIR / "build", ROOT_DIR / "dist"):
        if folder.exists():
            shutil.rmtree(folder)
            print(f"Removed: {folder}")


def build_exe():
    """Build the executable with PyInstaller."""

    _clean_build_artifacts()

    cmd = _get_pyinstaller_command() + [
        "--console",
        "--onefile",
        "--name", APP_NAME,
        "--clean",
        "--noupx",
        "--collect-all", "yt_dlp",
        # Version info
        "--version-file", str(VERSION_FILE),
        # Hidden imports for new modules
        "--hidden-import", "core.async_manager",
        "--hidden-import", "core.database",
        "--hidden-import", "core.downloader",
        "--hidden-import", "core.config",
        "--hidden-import", "core.history",
        "--hidden-import", "core.errors",
        "--hidden-import", "core.network",
        "--hidden-import", "core.utils",
        "--hidden-import", "core.dependencies",
        "--hidden-import", "core.logger",
        "--hidden-import", "ui.main_window",
        "--hidden-import", "ui.styles",
        "--hidden-import", "ui.components.title_bar",
        "--hidden-import", "ui.components.history_dialog",
        "--log-level", "WARN",
        str(ENTRY_POINT)
    ]

    icon_path = ROOT_DIR / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    else:
        print("Warning: icon.ico not found, building without icon")

    ffmpeg_path = ROOT_DIR / "ffmpeg.exe"
    if ffmpeg_path.exists():
        cmd.extend(["--add-binary", f"{ffmpeg_path};."])
    else:
        print("Warning: ffmpeg.exe not found, building without bundled ffmpeg")

    aria2c_path = ROOT_DIR / "aria2c.exe"
    if aria2c_path.exists():
        cmd.extend(["--add-binary", f"{aria2c_path};."])
    else:
        print("Warning: aria2c.exe not found, building without bundled aria2c")

    print("Building YTDLE executable...")
    print(f"Version: {VERSION}")
    print(f"Author: {AUTHOR}")
    print(f"Working directory: {ROOT_DIR}")
    if os.environ.get("YTDLE_USE_UPX", "").strip().lower() in {"1", "true", "yes"}:
        cmd = [arg for arg in cmd if arg != "--noupx"]
        print("UPX enabled via YTDLE_USE_UPX=1")
    else:
        print("UPX disabled (default) to avoid compression failures on system DLLs")
    print()

    result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=False)

    if result.returncode == 0:
        print("\n" + "="*60)
        print("Build successful!")
        print(f"Executable: {ROOT_DIR / 'dist' / f'{APP_NAME}.exe'}")
        print("="*60)
        return True
    else:
        print("\nBuild failed!")
        return False


def create_version_info():
    """Create version info file for Windows executable metadata."""
    file_version = _python_file_version(VERSION)
    version_info = f'''VSVersionInfo(
  ffi=FixedFileInfo(
        filevers=({file_version}),
        prodvers=({file_version}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{AUTHOR}'),
        StringStruct(u'FileDescription', u'{DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{VERSION}'),
        StringStruct(u'InternalName', u'YTDLE'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 {AUTHOR}'),
        StringStruct(u'OriginalFilename', u'YTDLE.exe'),
        StringStruct(u'ProductName', u'YTDLE Media Downloader'),
        StringStruct(u'ProductVersion', u'{VERSION}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(version_info)

    print(f"Created {VERSION_FILE}")


if __name__ == "__main__":
    create_version_info()
    success = build_exe()
    sys.exit(0 if success else 1)
