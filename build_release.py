#!/usr/bin/env python3
"""
Build script for YTDLE release with full metadata.
"""

import subprocess
import sys
import os

VERSION = "2.0.0"
AUTHOR = "Master0fFate"
DESCRIPTION = "YTDLE Media Downloader - Modern GUI/CLI downloader built with Python and PySide6"


def build_exe():
    """Build the executable with PyInstaller."""

    # Clean previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)

    for f in os.listdir("."):
        if f.endswith(".spec"):
            os.remove(f)

    cmd = [
        "pyinstaller",
        "--console",
        "--onefile",
        "--name", "YTDLE",
        "--clean",
        "--collect-all", "yt_dlp",
        "--icon", "icon.ico",
        "--add-binary", "ffmpeg.exe;.",
        "--add-binary", "aria2c.exe;.",
        # Version info
        "--version-file", "version_info.txt",
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
        "main.py"
    ]

    print("Building YTDLE executable...")
    print(f"Version: {VERSION}")
    print(f"Author: {AUTHOR}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print("\n" + "="*60)
        print("Build successful!")
        print(f"Executable: dist\\YTDLE.exe")
        print("="*60)
        return True
    else:
        print("\nBuild failed!")
        return False


def create_version_info():
    """Create version info file for Windows executable metadata."""
    version_info = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('.', ', ')}, 0),
    prodvers=({VERSION.replace('.', ', ')}, 0),
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
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025 {AUTHOR}'),
        StringStruct(u'OriginalFilename', u'YTDLE.exe'),
        StringStruct(u'ProductName', u'YTDLE Media Downloader'),
        StringStruct(u'ProductVersion', u'{VERSION}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''

    with open("version_info.txt", "w") as f:
        f.write(version_info)

    print("Created version_info.txt")


if __name__ == "__main__":
    create_version_info()
    success = build_exe()
    sys.exit(0 if success else 1)
