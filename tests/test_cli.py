import argparse
from pathlib import Path

import pytest

import core.cli as cli
import main as app_main
from core.history import DownloadHistory


def _saved(tmp_path: Path, **overrides) -> cli.SavedDownloadSettings:
    values = {
        "directory": str(tmp_path / "downloads"),
        "is_mp3": True,
        "quality": "320k",
        "download_playlist": False,
        "restrict_filenames": False,
        "use_async": True,
        "use_aria2c": False,
        "output_template": "%(title).150s",
        "ffmpeg_args": "",
        "ffmpeg_mode": "Append",
        "cookie_source": "none",
        "cookie_file": "",
        "browser_profile": "",
        "browser_keyring": "",
        "browser_container": "",
    }
    values.update(overrides)
    return cli.SavedDownloadSettings(**values)


def _download_args(*values: str) -> argparse.Namespace:
    parser = cli.build_parser()
    return parser.parse_args(["download", *values])


def test_collect_urls_reads_utf8_lists_and_reports_non_url_lines(tmp_path, capsys):
    url_file = tmp_path / "batch.txt"
    url_file.write_text(
        "\ufeff# first line\n"
        "https://example.test/one\n"
        "\n"
        "https://example.test/one\n"
        "https://example.test/two\n",
        encoding="utf-8",
    )

    urls = cli.collect_urls(_download_args("--input-file", str(url_file)))

    assert urls == [
        "https://example.test/one",
        "https://example.test/one",
        "https://example.test/two",
    ]
    output = capsys.readouterr().out
    assert "ignored 1 blank line(s) and 1 comment line(s)" in output
    assert "1 duplicate URL occurrence(s) will be downloaded" in output


def test_collect_urls_rejects_every_invalid_item_before_download(tmp_path):
    url_file = tmp_path / "invalid.txt"
    url_file.write_text(
        "https://example.test/ok\nftp://example.test/no\nnot a url\n",
        encoding="utf-8",
    )

    try:
        cli.collect_urls(_download_args("--input-file", str(url_file)))
    except cli.CliValidationError as error:
        message = str(error)
    else:
        raise AssertionError("Invalid input should raise CliValidationError")

    assert "ftp://example.test/no" in message
    assert "not a url" in message
    assert "must start with http:// or https://" in message
    assert "contains spaces" in message


def test_resolve_download_config_uses_saved_values_and_explicit_overrides(tmp_path):
    saved = _saved(
        tmp_path,
        is_mp3=False,
        quality="720p",
        download_playlist=True,
        restrict_filenames=True,
        use_async=False,
        output_template="%(uploader)s/%(title)s",
    )
    args = _download_args(
        "--format",
        "mp3",
        "--quality",
        "192k",
        "--no-playlist",
        "--no-restrict-filenames",
        "--async",
        "--connections",
        "8",
        "--concurrent-downloads",
        "4",
    )

    config = cli.resolve_download_config(args, saved)

    assert config.options.is_mp3 is True
    assert config.options.quality == "192k"
    assert config.options.download_playlist is False
    assert config.options.restrict_filenames is False
    assert config.use_async is True
    assert config.options.max_connections == 8
    assert config.max_concurrent_downloads == 4
    assert config.options.outtmpl_template == "%(uploader)s/%(title)s"


def test_resolve_download_config_resets_saved_quality_when_format_changes(tmp_path):
    config = cli.resolve_download_config(
        _download_args("--format", "mp4"),
        _saved(tmp_path, is_mp3=True, quality="128k"),
    )

    assert config.options.is_mp3 is False
    assert config.options.quality == "Best"


def test_resolve_download_config_rejects_quality_for_wrong_format(tmp_path):
    try:
        cli.resolve_download_config(
            _download_args("--format", "mp4", "--quality", "192k"),
            _saved(tmp_path),
        )
    except cli.CliValidationError as error:
        assert "Invalid MP4 resolution" in str(error)
    else:
        raise AssertionError("Wrong quality should raise CliValidationError")


def test_direct_download_shorthand_forwards_validated_batch_without_network(
    tmp_path, monkeypatch
):
    captured = {}

    def fake_run_download(urls, config, history_file):
        captured["urls"] = urls
        captured["config"] = config
        captured["history_file"] = history_file
        return 0

    monkeypatch.setattr(cli, "run_download", fake_run_download)

    result = cli.run_cli(
        [
            "--url",
            "https://example.test/one",
            "--url",
            "https://example.test/two",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--format",
            "mp4",
            "--quality",
            "720p",
            "--no-async",
            "--no-aria2c",
            "--no-cookies",
        ]
    )

    assert result == 0
    assert captured["urls"] == ["https://example.test/one", "https://example.test/two"]
    assert captured["config"].use_async is False
    assert captured["config"].options.quality == "720p"


def test_download_failures_are_reported_and_return_nonzero(tmp_path, monkeypatch, capsys):
    class FailingManager:
        def __init__(self, _urls, _options, **callbacks):
            self.callbacks = callbacks

        def cancel(self):
            pass

        def run(self):
            url = "https://example.test/failure"
            self.callbacks["on_item_started"](url)
            self.callbacks["on_error"]("Error downloading test item")
            self.callbacks["on_item_finished"](url, False, "network failed")
            self.callbacks["on_all_finished"](0, 1)

    import core.downloader as downloader

    monkeypatch.setattr(downloader, "DownloadManager", FailingManager)
    monkeypatch.setattr(cli, "setup_logging", lambda **_kwargs: None)
    config = cli.resolve_download_config(
        _download_args("--no-async", "--no-cookies", "--no-aria2c"),
        _saved(tmp_path),
    )

    result = cli.run_download(
        ["https://example.test/failure"],
        config,
        str(tmp_path / "history.db"),
    )

    output = capsys.readouterr()
    assert result == 1
    assert "FAILED: https://example.test/failure" in output.err
    assert "Batch complete. Success: 0, Failed: 1." in output.out


def test_legacy_short_flags_remain_compatible(tmp_path, monkeypatch):
    captured = {}

    def fake_run_download(urls, config, history_file):
        captured["urls"] = urls
        captured["config"] = config
        return 0

    monkeypatch.setattr(cli, "run_download", fake_run_download)

    result = cli.run_cli(
        [
            "-i",
            "https://example.test/legacy",
            "-od",
            str(tmp_path / "downloads"),
            "-f",
            "mp3",
            "-q",
            "192k",
            "-t",
            "%(uploader)s/%(title)s",
            "-p",
            "-r",
            "-v",
            "--no-aria2c",
            "--no-cookies",
        ]
    )

    assert result == 0
    config = captured["config"]
    assert captured["urls"] == ["https://example.test/legacy"]
    assert config.options.directory == str((tmp_path / "downloads").resolve())
    assert config.options.is_mp3 is True
    assert config.options.quality == "192k"
    assert config.options.outtmpl_template == "%(uploader)s/%(title)s"
    assert config.options.download_playlist is True
    assert config.options.restrict_filenames is True
    assert config.verbose is True


def test_main_routes_any_arguments_to_terminal_entry(monkeypatch):
    received = {}

    def fake_run_cli(argv):
        received["argv"] = argv
        return 7

    monkeypatch.setattr(app_main, "run_cli", fake_run_cli)
    monkeypatch.setattr(app_main.sys, "argv", ["main.py", "tools", "--output", "json"])

    with pytest.raises(SystemExit) as exit_info:
        app_main.main()

    assert exit_info.value.code == 7
    assert received["argv"] == ["tools", "--output", "json"]


def test_download_without_inputs_returns_actionable_usage_error(tmp_path, capsys):
    result = cli.run_cli(
        [
            "download",
            "--output-dir",
            str(tmp_path / "downloads"),
            "--no-aria2c",
            "--no-cookies",
        ]
    )

    assert result == 2
    assert "No download input was provided" in capsys.readouterr().err


def test_settings_command_persists_gui_compatible_values(tmp_path, monkeypatch, capsys):
    class MemorySettings:
        values = {}

        def __init__(self, *_args):
            pass

        def value(self, key, default=None, type=None):
            return self.values.get(key, default)

        def setValue(self, key, value):
            self.values[key] = value

        def sync(self):
            pass

    monkeypatch.setattr(cli, "QSettings", MemorySettings)

    result = cli.run_cli(
        [
            "settings",
            "--output-dir",
            str(tmp_path / "saved-downloads"),
            "--format",
            "mp4",
            "--quality",
            "720p",
            "--no-playlist",
            "--no-async",
            "--no-aria2c",
            "--no-cookies",
            "--output",
            "json",
        ]
    )

    assert result == 0
    assert MemorySettings.values["is_mp3"] is False
    assert MemorySettings.values["quality"] == "720p"
    assert MemorySettings.values["use_async"] is False
    assert MemorySettings.values["cookie_browser"] == "None"
    assert '"format": "mp4"' in capsys.readouterr().out


def test_history_lists_exports_and_requires_confirmation_to_clear(tmp_path, capsys):
    history_path = tmp_path / "history.db"
    history = DownloadHistory(str(history_path))
    history.add_completed(
        "https://example.test/complete",
        "Complete",
        "mp4",
        "720p",
        str(tmp_path / "complete.mp4"),
    )
    history.add_failed(
        "https://example.test/fail",
        "Failure",
        "mp3",
        "192k",
        "network failed",
    )
    history.close()

    assert (
        cli.run_cli(
            ["history", "--history-file", str(history_path), "--status", "failed"]
        )
        == 0
    )
    assert "https://example.test/fail" in capsys.readouterr().out

    exported = tmp_path / "failed.txt"
    assert (
        cli.run_cli(
            [
                "history",
                "--history-file",
                str(history_path),
                "--export-failed",
                str(exported),
            ]
        )
        == 0
    )
    assert "https://example.test/fail" in exported.read_text(encoding="utf-8")

    assert (
        cli.run_cli(
            ["history", "--history-file", str(history_path), "--clear", "failed"]
        )
        == 2
    )
    assert "--yes to confirm" in capsys.readouterr().err

    assert (
        cli.run_cli(
            [
                "history",
                "--history-file",
                str(history_path),
                "--clear",
                "failed",
                "--yes",
            ]
        )
        == 0
    )
    history = DownloadHistory(str(history_path))
    try:
        assert history.get_failed() == []
        assert len(history.get_completed()) == 1
    finally:
        history.close()
