# Third-party notices

YTDLE release executables aggregate the following independent command-line programs. They remain separate works invoked as external tools and are not authored by or endorsed by YTDLE.

## FFmpeg

- Version: `2026-09-10-git-fd7c73d01e-full_build-www.gyan.dev`
- Project: https://ffmpeg.org/
- Windows build provider: https://www.gyan.dev/ffmpeg/builds/
- Corresponding source commit: https://github.com/FFmpeg/FFmpeg/commit/fd7c73d01e
- License: GNU General Public License version 3 (GPLv3), as reported by the distributed full build.

## aria2

- Version: `1.37.0`
- Project and corresponding source tag: https://github.com/aria2/aria2/tree/release-1.37.0
- License: GNU General Public License version 2 or later (GPL-2.0-or-later).

## Node.js

- Version: `22.22.2`
- Project: https://nodejs.org/
- License: MIT. Node.js is bundled as the JavaScript runtime required by `yt-dlp-ejs` for YouTube challenge solving.

Exact package and executable checksums are recorded in `BINARY_PROVENANCE.md`.

## Roboto

- Project: https://github.com/google/fonts/tree/main/ofl/roboto
- License: SIL Open Font License 1.1 (`assets/ROBOTO-OFL.txt`, bundled in release EXEs).
- Use: variable Roboto font for desktop interface typography.
- Vendored font SHA-256: `d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134`.

## Material Icons

- Project: https://github.com/google/material-design-icons
- License: Apache License 2.0
- Use: outlined 24px glyphs vendored into `ui/icons.py` for desktop chrome.
