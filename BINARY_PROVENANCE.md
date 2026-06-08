# Binary Provenance

YTDLE can bundle `ffmpeg.exe` and `aria2c.exe` for Windows release builds, but the executables are intentionally ignored by Git. This keeps the repository small and prevents accidental uploads of 100MB+ local binaries while still allowing reproducible release checks.

## Current trusted sources

| Tool | Expected version | Source | Notes |
| --- | --- | --- | --- |
| FFmpeg | `2026-06-04-git-c27a3b12e3` or newer | https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z | Gyan.dev Windows GPL full build. Package SHA-256 on 2026-06-08: `9c46e551b1f52c4a6858e98f03689e61c4ddeac54b1988c41731ef399abf4266`. Extracted local `ffmpeg.exe` SHA-256 after update: `5225b577b2896e91c40bac6cdd6d3d116e48d4ea3ceebd90c4bb475786e2e184`. |
| aria2c | `1.37.0` | https://github.com/aria2/aria2/releases/tag/release-1.37.0 | Official aria2 release. Current local binary already reports `aria2 version 1.37.0`. |

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

- `build_release.py` bundles these binaries when they are present locally. If either is missing, the build still succeeds but prints a warning and the executable depends on a system-installed tool.
