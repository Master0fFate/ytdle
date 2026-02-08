# YTDLE Media Downloader

YTDLE is a modern, cross-platform media downloader built with Python and PySide6 (Qt). It provides a user-friendly graphical interface for `yt-dlp`, allowing users to download videos and audio from thousands of supported sites including YouTube, Twitter, TikTok, and more.

## Features

- **Modern UI**: Clean, dark-themed interface designed with PySide6.
- **Async Download Engine**: High-performance asyncio-based downloader with lower memory overhead and better concurrency.
- **CLI Mode**: Full command-line interface for headless usage or scripting.
- **Format Selection**: Easily switch between MP3 (Audio) and MP4 (Video) formats.
- **Quality Control**: Select specific bitrates for audio or resolution caps for video (up to 4K/8K).
- **Aria2c Integration**: Optional multi-connection downloading for 3-5x faster speeds.
- **Custom FFmpeg Args**: Pass custom flags directly to FFmpeg (via GUI or CLI).
- **Batch Processing**: Download multiple URLs concurrently with a queue system.
- **Playlist Support**: Option to download entire playlists or channels.
- **Smart Naming**: Customizable output filename templates (e.g., Uploader - Title).
- **Robust Error Handling**: Automatic retries and fallback logic for different formats.
- **Logging**: Detailed file logging for troubleshooting.
- **Download History**: Persistent SQLite-based history tracking with export and retry failed downloads.
- **Network Detection**: Real-time network connectivity monitoring with manual check capability.
- **Download Controls**: Pause, resume, skip, and cancel downloads with thread-safe controls.

## Requirements

- **Python 3.10+**
- **FFmpeg**: Required for audio extraction and format merging. The `ffmpeg.exe` binary must be available in the system PATH or placed alongside the application executable.
- **Aria2c** (Optional): For multi-connection downloads. Download from [aria2 releases](https://github.com/aria2/aria2/releases).

## Installation & Running from Source

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Master0fFate/ytdle.git
    cd ytdle
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python main.py
    ```

## Usage

### Graphical Interface (GUI)
Run `YTDLE.exe` or `python main.py` to launch the modern dark-themed GUI.

**New Options:**
- **Async Mode**: Enable high-performance asyncio download engine (default: enabled)
- **Use Aria2c**: Enable multi-connection downloads for faster speeds (requires aria2c binary)

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
3.  Select build type:
    -   **Standard**: Smaller executable, requires external binaries
    -   **Standalone**: Bundles FFmpeg for out-of-the-box usage
    -   **Full Standalone**: Bundles both FFmpeg and Aria2c
4.  The script will generate `YTDLE.exe` in the `dist` folder.

### Method 2: Manual Compilation

**Standard Build:**
```bash
pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp main.py
```

**Bundled Build (with FFmpeg):**
```bash
pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp --add-binary "ffmpeg.exe;." main.py
```

**Full Bundled Build (with FFmpeg and Aria2c):**
```bash
pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp --add-binary "ffmpeg.exe;." --add-binary "aria2c.exe;." main.py
```

### Note on External Binaries

- **Standard Build**: The executable is smaller but requires `ffmpeg.exe` to be in the same folder or in your System PATH.
- **Standalone Build**: The executable is larger but works out-of-the-box on any machine without extra setup.
- **Aria2c**: Optional binary for multi-connection downloads. Place `aria2c.exe` alongside the executable or in PATH.

## Project Structure

- `core/`: Backend logic, configuration, and downloader engine.
  - `async_manager.py`: Asyncio-based download manager for high-performance concurrent downloads.
  - `database.py`: SQLite database manager for persistent history storage.
  - `downloader.py`: Legacy threading-based download manager (still supported).
  - `history.py`: Download history tracking with SQLite backend and JSON fallback.
  - `config.py`: Configuration dataclasses and options.
  - `errors.py`: Custom exceptions and error classification.
  - `network.py`: Network connectivity monitoring utilities.
- `ui/`: User interface components, styles, and main window logic.
  - `components/`: Reusable UI components (History dialog, Title bar, etc.).
- `main.py`: Application entry point (handles both GUI and CLI).
- `build.bat`: Windows build script with multiple build options.
- `requirements.txt`: Production dependencies.
- `requirements-dev.txt`: Development dependencies (testing, linting).

## Architecture

YTDLE uses a modular architecture with clear separation of concerns:

**Download Engine**: Choose between legacy threading (`DownloadManager`) or modern asyncio (`AsyncDownloadManager`) based on your needs. The async engine provides better scalability and lower memory usage.

**Storage**: SQLite database with WAL mode for concurrent read/write operations. Automatic migration from legacy JSON format with backup.

**External Tools**: yt-dlp handles the actual downloading, with optional aria2c for multi-connection acceleration and FFmpeg for post-processing.

## License

This project is open source. See the repository for license details.
