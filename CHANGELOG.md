# Changelog

## 2.4.0 - 2026-09-13

### Desktop

- Rebuilt the GUI as a hard-edged Angelcore workspace: square corners, mono type, Google Material outlined icons, and purple only on the primary action, focus, tabs, progress, and checked switches.
- Removed the light-gray cages around fields and buttons. Idle fields use a one-sided hairline; Windows native white bevels are flattened.

### Toolchain

- Bundled FFmpeg updated to `2026-09-10-git-fd7c73d01e` (Gyan.dev full build).
- Confirmed yt-dlp `2026.8.19`, yt-dlp-ejs `0.8.0`, and aria2c `1.37.0` are still the current upstream releases.

## 2.3.0 - 2026-08-22

### Added

- A full terminal interface (`YTDLE COMMAND`) with `download`, `retry-failed`, `history`, `check-network`, `tools`, and `settings` commands. `YTDLE --url ...` still works as a download shorthand.
- `YTDLE download` reads repeated `--url` flags, inline `--input` URLs, and UTF-8 `--input-file` lists (including `-` for standard input) with comment, blank-line, duplicate, and URL validation before anything starts.
- `YTDLE history` lists, searches, filters, exports failed URLs, and clears records; `YTDLE retry-failed` redownloads every failed record with optional setting overrides.
- The terminal interface reads and writes the exact GUI settings, so both front-ends share one configuration, cookie policy, and download history.
- `--cookies-from-browser`, `--cookies-file`, and `--no-cookies` flags with profile, keyring, and container options for both the CLI and the GUI cookie model.

### Changed

- The cookie selector now has an explicit `Cookie File (Fallback)` source. Exactly one cookie source is used: none, the cookie file, or one browser. Old configurations that saved a file while `None` was selected keep working.
- Profile, keyring, and container fields are only enabled when a real browser is selected, and cookie decisions are reported in the activity console.
- yt-dlp minimum raised to `2026.8.19` and `yt-dlp-ejs` added as a required dependency for reliable YouTube challenge solving.

### Distribution

- The release executable now bundles the Node.js runtime that `yt-dlp-ejs` needs, so JavaScript challenges keep working on machines without Node.js installed.
- Release builds run PyInstaller from the active Python environment to keep yt-dlp and its solver in one package.
- Added regression coverage for the CLI, cookie sources, yt-dlp-ejs bundling, and cookie precedence in the shared option builder.

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
