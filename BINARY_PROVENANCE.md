# Binary Provenance

YTDLE can bundle `ffmpeg.exe` and `aria2c.exe` for Windows release builds, but the executables are intentionally ignored by Git. This keeps the repository small and prevents accidental uploads of 100MB+ local binaries while still allowing reproducible release checks.

## Current trusted sources

| Tool | Expected version | Source | Notes |
| --- | --- | --- | --- |
| FFmpeg | `2026-10-01-git-0b01ed76aa` | https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z | Gyan.dev Windows 64-bit static GPLv3 full build, linked by FFmpeg's official download page. Archive SHA-256 on 2026-10-05: `da89007b937a103b0d8b5591f82116d0f5d01d6efd284a9cbdda7eb103a3e081` (matches Gyan.dev's published `.sha256`). Extracted `ffmpeg.exe` SHA-256: `584d65c96d3a8f5e4d70d23ba7bb555ca6b267ba3f453046c4ed9e0c97e74fac`. Smoke-tested MP3 (libmp3lame) and H.264 (libx264) encodes. Source commit: https://github.com/FFmpeg/FFmpeg/commit/0b01ed76aa. |
| aria2c | `1.37.0` | https://github.com/aria2/aria2/releases/tag/release-1.37.0 | Official signed aria2 release and still the newest upstream release on 2026-10-05. Windows 64-bit archive SHA-256: `67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288`. Extracted `aria2c.exe` SHA-256: `be2099c214f63a3cb4954b09a0becd6e2e34660b886d4c898d260febfe9d70c2`. The refreshed official binary is byte-identical to the previous local copy. |
| Node.js | `22.22.2` | https://nodejs.org/dist/v22.22.2/ | Official Windows x64 Node.js runtime bundled for `yt-dlp-ejs`. Extracted `node.exe` SHA-256: `ae1a50511be58e987483fdbc12125407443926d2d394669ade2352776e920dd3`. |

## Update status (2026-10-05)

FFmpeg was refreshed to the 2026-10-01 Gyan.dev git build; the archive checksum matched the published value before extraction. aria2c 1.37.0 is still the latest official release, and the local `aria2c.exe` still matches the hash above. yt-dlp `2026.08.19` and yt-dlp-ejs `0.8.0` are the newest stable PyPI releases (a newer yt-dlp *nightly* exists; release builds stay on stable). Node.js was not part of this refresh.

## Release policy

- Keep `ffmpeg.exe` and `aria2c.exe` beside `main.py` for source builds or beside `YTDLE.exe` for standard release builds. The release builder packages the Node.js runtime found on `PATH` into the executable.
- Do not commit the executables. Commit source, tests, release scripts, and this provenance file instead.
- Before a standalone build, verify local binaries with:

```powershell
.\ffmpeg.exe -version
.\aria2c.exe --version
node --version
Get-FileHash .\ffmpeg.exe -Algorithm SHA256
Get-FileHash .\aria2c.exe -Algorithm SHA256
Get-FileHash (Get-Command node).Source -Algorithm SHA256
```

- `build_release.py` treats `icon.ico`, both executables, and `THIRD_PARTY_NOTICES.md` as mandatory release assets. A release build fails instead of silently producing an incomplete executable.
