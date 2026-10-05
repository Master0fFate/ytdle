# Changelog

## 2.7.0 - 2026-10-05

### Redesigned desktop app

- New layout that reads top to bottom: a link drop zone with a friendly empty state, one row for format, quality, and playlist, a "Save to" row, a status card, and an activity panel. Expert settings moved to new **Options** and **Cookies** pages, reached from a nav pill in the title bar (`Ctrl+1`/`2`/`3`).
- **Download** is now a large labeled button that counts your links ("Download 3"). While a batch runs it becomes pause, skip, and **Stop**.
- The status card states the plan before you start ("3 links · MP3 320k · to C:\Downloads") and the outcome after ("2 saved, 1 failed"). Validation problems appear in the card with the fix and move focus to the field; no more modal "Validation" box.
- New **Downloads** activity list: one row per link with Waiting / Downloading / Saved / Failed / Skipped / Not started, the saved path or the failure reason, and double-click to show the file in Explorer. The raw log stays one click away.
- Batch progress bar that combines concurrent items and never jumps backward, with smooth animation. The taskbar title shows the percentage, and the taskbar button flashes when a batch finishes in the background.
- `Paste` button and `Ctrl+Shift+V` add clipboard links through the same validation and de-duplication as imports. Dropped links now go through it too, instead of being inserted raw into the editor. Also new: `Ctrl+O` import and `Ctrl+H` history.
- Network status is a visible chip (Online / Offline). The toolchain (FFmpeg, aria2c, yt-dlp versions and origin) is visible on the Options page.
- Window drag uses the system move, so Windows snap works. Double-click the title bar to maximize, and resize from the bottom-right grip.
- Friendlier labels: file-name presets have names ("Uploader - Title") instead of raw templates, and the switches read "Whole playlist", "Safe file names (ASCII only)", "Parallel downloads", and "Multi-connection downloads (aria2c)". Saved settings carry over.
- Combo boxes show a dropdown chevron again. Disabled fields stay visible inside cards. Dialogs ask Windows for dark title bars.
- History: tab counts ("Failed (4)"), one search box that keeps its text across tabs, labeled action buttons, and a capped URL column so titles stay readable.

### Skins

- New **Skin** setting at the top of Options. It switches the whole window at once and is remembered:
  - **Default**: the redesigned look above.
  - **Material 3**: Google's Material 3 dark scheme done to spec: tonal surfaces, filled text fields with an indicator line, tabs with an underline, a light filled Download button with dark text, outlined segmented buttons, tonal Paste/Stop, the M3 switch, and a 4 px progress bar.
  - **Angelcore**: near-black, square, one monospace font, neutral inks only. Actions read as `[words]`, state as `[ok]` / `[!]` / `...` marks, switches as `[x]` / `[ ]`, the current page as `> Download`. Regions are split by hairlines with no boxed controls, Download is the one white fill, and the empty link list shows a faint dithered YTDLE mark.
- Labels, accessible names, shortcuts, and behavior are the same in every skin.

### Stress-tested with realistic worst-case data

A new dev-only UI lab (`python -m dev.ui_lab`) runs the real window with demo data or realistic worst cases (OneDrive paths, tracking-laden links, CJK/Arabic/Vietnamese/emoji titles, HTML-looking titles, 1,284 links, 10,000 history rows). It found and this release fixes:

- History showed every saved path as `C:…`. Paths and links now shorten in the middle, so the file name stays visible. Failure reasons show their first line without `ERROR:`. The redundant Status column is gone. Empty or "Unknown" titles show the link, and missing or 1970 dates show "—".
- History opens with the newest 2,000 records (**Load all** shows the rest), so a long history opens instantly.
- While a batch runs, and after it, the activity list gets most of the height. At the minimum size it showed one row of nine.
- The plan line shortens in the middle, so the folder name is no longer cut off.
- Counts use your locale's digit grouping ("1,284 links").
- No stray focus ring on the open-folder button when a download starts.
- No light square in the corner of the link list when both scrollbars show.
- Cookie sources have readable names ("Firefox", "No cookies"); saved settings carry over. The Linux-only keyring field is hidden on other systems.
- Titles that look like HTML (`<b>Live</b>`) stay literal in tooltips.
- Switches that are on but disabled during a download keep a dimmed accent, so on and off still differ.
- On small or high-DPI screens (1280 × 720 at 125%, 1080p at 200%) the window now fits: the minimum height follows the screen, down to 480 px.
- YouTube links to the same video (`youtu.be/…`, `watch?v=…&si=…`, Shorts) count as one link. Links that name a playlist stay separate.
- File paths on Windows are capped below the 260-character limit, so long OneDrive folders plus long titles no longer fail with "No such file".
- Text fields have sensible length limits.

### Download engine fixes

- Cancelling a batch of more than six links no longer hangs the app; the queue is drained so the batch always finishes.
- Resume (and cancel while paused) no longer deadlocks; the pause gate is changed thread-safely on the download loop.
- Pause now holds downloads that are already running, not only the ones that have not started.
- HLS/DASH (fragment) downloads now report progress and obey cancel and skip; the progress hook is bound to its item instead of thread-local state.
- Skip affects only the items running at that moment, and skipped or cancelled items are no longer retried three times.
- Missing, private, or login-only videos fail at once instead of being extracted three times (both engines).
- Live speed/ETA updates are throttled to four per second per item.
- `retry-failed` and History's **Retry failed** add each link once and skip links whose latest attempt succeeded.
- New history rows are stored in local time, like migrated rows (SQLite's default was UTC). The legacy JSON migration no longer re-imports on every launch when a backup file already exists.

### Toolchain

- Bundled FFmpeg updated to `2026-10-01-git-0b01ed76aa` (Gyan.dev full build; checksum recorded in `BINARY_PROVENANCE.md`). aria2c `1.37.0`, yt-dlp `2026.08.19`, and yt-dlp-ejs `0.8.0` are already the newest stable releases.

## 2.6.0 - 2026-09-27

### Desktop polish

- Made the title bar tall enough for its window buttons, so their circular backgrounds and full click targets stay inside the window.
- Reworked vertical and horizontal scrollbars with quiet tracks, rounded thumbs, and clearer hover/drag feedback instead of bright native handles.
- Put a little more room between the Completed/Failed tabs and the history table.
- Updated the desktop screenshot to show the corrected layout.

## 2.5.0 - 2026-09-27 (local build; changes included in 2.6.0)

### Desktop

- Replaced the hard-edged theme with a dark Qt adaptation of Material 3 Expressive: tonal surfaces, Roboto, rounded filled fields with a focus underline, joined format selection, and purple primary action. The accent remains `#7c3aed`.
- Queue, history, network, and transport actions are icon-only with tooltips and accessible names; settings and status retain visible words.
- Moved queue actions beside the directory controls, combined utility and transport actions into one row, and matched the download button size to its neighbors. Verified 920 × 620 and 760 × 560 layouts without control overlap.
- Limited the on-screen activity document to its latest 1,500 lines; the file log and SQLite history remain unchanged.

### Dependencies and release

- Raised the PySide6 minimum to `6.11.2`, pytest to `9.1.1`, Ruff to `0.16.9`, and PyInstaller to `6.22.3`; recorded the project's existing error-check rule set in `ruff.toml`. yt-dlp `2026.8.19`, yt-dlp-ejs `0.8.0`, and pytest-qt `4.5.0` were already current on the package index at build time.
- Included the Roboto font and its SIL OFL license in release builds, with a fresh desktop screenshot in the README.
- Kept the previously verified FFmpeg/Node.js binaries after a newer FFmpeg archive download stalled; see `BINARY_PROVENANCE.md` for the external-binary update status.

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
