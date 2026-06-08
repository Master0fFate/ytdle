from pathlib import Path

from core.utils import get_tool_path


def test_get_tool_path_prefers_explicit_app_owned_directory(tmp_path: Path):
    tool = tmp_path / "aria2c.exe"
    tool.write_bytes(b"placeholder")

    assert get_tool_path("aria2c.exe", extra_dirs=[tmp_path]) == str(tool.resolve())


def test_get_tool_path_does_not_search_arbitrary_cwd(tmp_path: Path, monkeypatch):
    tool = tmp_path / "ffmpeg.exe"
    tool.write_bytes(b"placeholder")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("shutil.which", lambda _name: None)

    assert get_tool_path("ffmpeg.exe") != str(tool.resolve())
