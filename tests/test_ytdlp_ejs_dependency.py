from importlib.metadata import version
from pathlib import Path

import build_release


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split(".") if part.isdigit())


def test_ytdlp_ejs_is_installed_for_youtube_challenge_solving():
    assert _version_tuple(version("yt-dlp")) >= (2026, 8, 19)
    assert _version_tuple(version("yt-dlp-ejs")) >= (0, 8, 0)


def test_release_build_collects_ytdlp_ejs_code_and_metadata():
    build_script = Path("build_release.py").read_text(encoding="utf-8")

    assert '"yt_dlp_ejs"' in build_script
    assert '"yt-dlp-ejs"' in build_script
    assert '"--specpath"' in build_script
    assert "_resolve_node_path" in build_script
    assert "node.exe" in build_script


def test_release_build_uses_the_active_python_environment(monkeypatch):
    monkeypatch.setattr(build_release.sys, "executable", "C:/venv/python.exe")

    assert build_release._get_pyinstaller_command() == [
        "C:/venv/python.exe",
        "-m",
        "PyInstaller",
    ]


def test_release_build_resolves_node_from_path(monkeypatch):
    monkeypatch.setattr(build_release.sys, "platform", "win32")
    monkeypatch.setattr(
        build_release.shutil, "which", lambda executable: f"C:/tools/{executable}"
    )

    assert build_release._resolve_node_path() == "C:/tools/node.exe"
