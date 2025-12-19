# YTDLE Media Downloader

YTDLE is a modern, cross-platform media downloader built with Python and PySide6 (Qt). It provides a user-friendly graphical interface for `yt-dlp`, allowing users to download videos and audio from thousands of supported sites including YouTube, Twitter, TikTok, and more.

## Features

- **Modern UI**: Clean, dark-themed interface designed with PySide6.
- **CLI Mode**: Full command-line interface for headless usage or scripting.
- **Format Selection**: Easily switch between MP3 (Audio) and MP4 (Video) formats.
- **Quality Control**: Select specific bitrates for audio or resolution caps for video (up to 4K/8K).
- **Custom FFmpeg Args**: Pass custom flags directly to FFmpeg (via GUI or CLI).
- **Batch Processing**: Download multiple URLs concurrently with a queue system.
- **Playlist Support**: Option to download entire playlists or channels.
- **Smart Naming**: Customizable output filename templates (e.g., Uploader - Title).
- **Robust Error Handling**: Automatic retries and fallback logic for different formats.
- **Logging**: Detailed file logging for troubleshooting.

## Requirements

- **Python 3.10+**
- **FFmpeg**: Required for audio extraction and format merging. The `ffmpeg.exe` binary must be available in the system PATH or placed alongside the application executable.

## Installation & Running from Source

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ytdle-dev.git
    cd ytdle-dev
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is missing, manually install: `pip install PySide6 yt-dlp`)*

3.  **Run the application**:
    ```bash
    python main.py
    ```

## Usage

### Graphical Interface (GUI)
Run `YTDLE.exe` to launch the modern dark-themed GUI.

### Command Line Interface (CLI)
You can use the **same** executable for CLI operations.

**Basic Usage:**
```bash
YTDLE.exe -i "https://youtube.com/watch?v=..."
```

**Options:**

| Argument | Description | Example |
| :--- | :--- | :--- |
| `-i`, `--input` | Input URL(s) (space separated) | `-i "url1" "url2"` |
| `-od`, `--output-dir` | Output directory (default: current) | `-od "C:\Downloads"` |
| `-f`, `--format` | Format (`mp3` or `mp4`, default: `mp3`) | `-f mp4` |
| `-q`, `--quality` | Quality (e.g., `192k`, `1080p`, `Best`) | `-q 1080p` |
| `-p`, `--playlist` | Download entire playlist | `-p` |
| `-r`, `--restrict` | Restrict filenames to ASCII | `-r` |
| `-t`, `--template` | Output filename template | `-t "%(uploader)s - %(title)s"` |
| `--no-check-certificate` | Disable SSL validation | `--no-check-certificate` |
| `--cookies` | Path to cookies file (anti-bot) | `--cookies cookies.txt` |
| `--ffmpeg-add-args` | Append FFmpeg arguments | `--ffmpeg-add-args "-vcodec libx264"` |
| `--ffmpeg-override-args` | Override FFmpeg arguments | `--ffmpeg-override-args "-vn"` |
| `-v`, `--verbose` | Enable verbose logging | `-v` |

**Examples:**

Download video as MP4 (1080p) to specific folder:
```bash
YTDLE.exe -i "https://youtu.be/..." -f mp4 -q 1080p -od "C:\MyVideos"
```

Download playlist as MP3 (320k):
```bash
YTDLE.exe -i "https://youtube.com/playlist?list=..." -f mp3 -q 320k -p
```

## Compiling to Executable

To build a standalone `.exe` file for Windows, use the provided build script or run PyInstaller manually.

### Method 1: Automatic Build Script (Recommended)
1.  Locate the `build.bat` file in the project root.
2.  Double-click `build.bat`.
3.  The script will generate:
    -   `YTDLE.exe` (Dual Mode: GUI + CLI)
    For both Standard and Bundled variants.

### Method 2: Manual Compilation

**Standard Build:**
```bash
pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp main.py
```

**Bundled Build:**
```bash
pyinstaller --console --onefile --name "YTDLE_bundled" --clean --collect-all yt_dlp --add-binary "ffmpeg.exe;." main.py
```

### Note on FFmpeg

- **Standard Build**: The executable is smaller but requires `ffmpeg.exe` to be in the same folder or in your System PATH.
- **Bundled Build**: The executable is larger but works out-of-the-box on any machine without extra setup.

## Project Structure

- `core/`: Backend logic, configuration, and downloader engine.
- `ui/`: User interface components, styles, and main window logic.
- `main.py`: Application entry point (handles both GUI and CLI).
- `YTDLE_old.py`: Archive of the original monolithic script.
