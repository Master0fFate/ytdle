# Binary Provenance

YTDLE can bundle `ffmpeg.exe` and `aria2c.exe` for Windows release builds, but the executables are intentionally ignored by Git. This keeps the repository small and prevents accidental uploads of 100MB+ local binaries while still allowing reproducible release checks.

## Current trusted sources

| Tool | Expected version | Source | Notes |
| --- | --- | --- | --- |
| FFmpeg | `2026-07-09-git-8de8405796` | https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z | Gyan.dev Windows 64-bit static GPLv3 full build, linked by FFmpeg's official download page. Archive SHA-256 on 2026-07-10: `cca96614a28aedc518bb1227015bce401aeb91c1b1ea341a7cb25a417a9dcef2`. Extracted `ffmpeg.exe` SHA-256: `3f6d578ee13c20488cc31bb1dcc4ac662527f8d8015273fea0c6a454d799b52c`. Source commit: https://github.com/FFmpeg/FFmpeg/commit/8de8405796. |
| aria2c | `1.37.0` | https://github.com/aria2/aria2/releases/tag/release-1.37.0 | Official signed aria2 release and newest upstream release as of 2026-07-10. Windows 64-bit archive SHA-256: `67d015301eef0b612191212d564c5bb0a14b5b9c4796b76454276a4d28d9b288`. Extracted `aria2c.exe` SHA-256: `be2099c214f63a3cb4954b09a0becd6e2e34660b886d4c898d260febfe9d70c2`. The refreshed official binary is byte-identical to the previous local copy. |

## Release policy

- Keep `ffmpeg.exe` and `aria2c.exe` beside `main.py` for source builds or beside `YTDLE.exe` for standard release builds.
- Do not commit the executables. Commit source, tests, release scripts, and this provenance file instead.
- Before a standalone build, verify local binaries with:

```powershell
.\ffmpeg.exe -version
.\aria2c.exe --version
Get-FileHash .\ffmpeg.exe -Algorithm SHA256
Get-FileHash .\aria2c.exe -Algorithm SHA256
```

- `build_release.py` treats `icon.ico`, both executables, and `THIRD_PARTY_NOTICES.md` as mandatory release assets. A release build fails instead of silently producing an incomplete executable.
