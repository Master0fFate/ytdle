# Changelog

## 2.2.1 - 2026-07-31

### Desktop experience

- Refined the interface into a compact zinc-and-purple workspace with a joined format selector, animated keyboard-accessible switches, monochrome icons, and action rows that remain usable at narrower window sizes.
- Moved toolchain, network, download, progress, and error messages into one activity console without flooding it with duplicate live updates.
- Made history loading and filtering smoother by querying once, retaining table rows, and refreshing only the history section that changed.

### Performance

- Removed blocking work from application startup with lazy downloader imports, asynchronous tool-version probes, and a cancellable non-blocking network check.
- Coalesced rapid settings writes, queue analysis, and repeated progress signals to keep typing and downloads responsive.
- Added reusable, thread-safe SQLite connections with explicit transaction rollback and deterministic shutdown.

### Reliability

- Record yt-dlp's final post-processed output paths for single items and playlists in both download engines.
- Detect an installed Deno, Node.js, or Bun runtime for yt-dlp and update the minimum yt-dlp version to `2026.7.4`.
- Strengthened queue parsing, history migration, logging failures, and application cleanup behavior.
- Expanded regression coverage for database concurrency, startup responsiveness, history filtering, output-path capture, progress coalescing, queue caching, and custom controls.

## 2.2.0 - 2026-07-10

### Added

- Smart URL queue with UTF-8 list import, HTTP(S) validation, duplicate detection, comment handling, and one-click cleanup.
- Unified queue ingestion for manual input, drag and drop, imported lists, and history retries.
- Queue diagnostics that identify invalid entries before a download starts.

### Performance and architecture

- Removed the duplicate yt-dlp metadata extraction pass, reducing extractor/network work from two calls to one per download attempt.
- Consolidated sync and async yt-dlp option construction into one shared policy module.
- Added deterministic coverage for single downloads, playlist-shaped results, and format fallback behavior.

### Reliability

- Replaced silent exception swallowing in touched download and UI cleanup paths with explicit handling and diagnostics.
- Fixed literal `\\n` output in queue ingestion, validation errors, and completion logs.
- Added focused queue parser and offscreen Qt integration tests.

### Distribution

- Updated bundled FFmpeg from `2026-06-04-git-c27a3b12e3` to `2026-07-09-git-8de8405796`.
- Refreshed aria2 from the official `1.37.0` Windows release; upstream has not published a newer stable version.
- Added verified archive and executable checksums plus third-party GPL notices.
- Hardened release builds to require the application icon, FFmpeg, aria2c, and third-party notices.
- Expanded generated-file and executable exclusions in `.gitignore`.
