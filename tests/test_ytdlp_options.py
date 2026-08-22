from core.config import DownloadOptions
import core.async_manager as async_manager
import core.downloader as downloader
import core.yt_dlp_options as yt_dlp_options


def _options(use_aria2c: bool = False) -> DownloadOptions:
    return DownloadOptions(
        is_mp3=False,
        quality="1080p",
        outtmpl_template="%(title).150s",
        directory="C:/Downloads",
        download_playlist=False,
        restrict_filenames=False,
        use_aria2c=use_aria2c,
        max_connections=8,
    )


def test_sync_options_include_resolved_ffmpeg_and_aria2c(monkeypatch):
    monkeypatch.setattr(
        yt_dlp_options, "get_ffmpeg_path", lambda: "C:/Tools/ffmpeg.exe"
    )
    monkeypatch.setattr(
        yt_dlp_options, "get_aria2c_path", lambda: "C:/Tools/aria2c.exe"
    )

    options = downloader.build_yt_dlp_options(
        _options(use_aria2c=True), lambda _data: None
    )

    assert options["ffmpeg_location"] == "C:/Tools/ffmpeg.exe"
    assert options["external_downloader"] == "C:/Tools/aria2c.exe"
    assert options["external_downloader_args"]["aria2c"][:4] == ["-x", "8", "-s", "8"]


def test_async_options_include_resolved_ffmpeg_and_aria2c(monkeypatch):
    monkeypatch.setattr(
        yt_dlp_options, "get_ffmpeg_path", lambda: "C:/Tools/ffmpeg.exe"
    )
    monkeypatch.setattr(
        yt_dlp_options, "get_aria2c_path", lambda: "C:/Tools/aria2c.exe"
    )

    options = async_manager.build_yt_dlp_options_async(
        _options(use_aria2c=True), lambda _data: None
    )

    assert options["ffmpeg_location"] == "C:/Tools/ffmpeg.exe"
    assert options["external_downloader"] == "C:/Tools/aria2c.exe"
    assert options["external_downloader_args"]["aria2c"][:4] == ["-x", "8", "-s", "8"]


def test_installed_javascript_runtime_is_forwarded_to_ytdlp(monkeypatch):
    monkeypatch.setattr(yt_dlp_options, "get_ffmpeg_path", lambda: None)
    monkeypatch.setattr(
        yt_dlp_options,
        "get_tool_path",
        lambda executable: (
            "C:/Program Files/nodejs/node.exe"
            if executable.lower() == "node.exe"
            else None
        ),
    )

    options = downloader.build_yt_dlp_options(
        _options(use_aria2c=False), lambda _data: None
    )

    assert options["js_runtimes"] == {
        "node": {"path": "C:/Program Files/nodejs/node.exe"}
    }


def test_aria2c_is_not_enabled_unless_requested(monkeypatch):
    monkeypatch.setattr(yt_dlp_options, "get_ffmpeg_path", lambda: None)
    monkeypatch.setattr(
        yt_dlp_options, "get_aria2c_path", lambda: "C:/Tools/aria2c.exe"
    )

    options = downloader.build_yt_dlp_options(
        _options(use_aria2c=False), lambda _data: None
    )

    assert "external_downloader" not in options


def test_both_engines_export_the_shared_builder():
    assert downloader.build_yt_dlp_options is yt_dlp_options.build_yt_dlp_options
    assert (
        async_manager.build_yt_dlp_options_async is yt_dlp_options.build_yt_dlp_options
    )

def test_cookie_source_precedence_in_shared_builder(monkeypatch):
    monkeypatch.setattr(yt_dlp_options, "get_ffmpeg_path", lambda: None)

    browser_only = downloader.build_yt_dlp_options(
        _options(), lambda _data: None
    )
    assert "cookiesfrombrowser" not in browser_only
    assert "cookiefile" not in browser_only

    file_opts = _options()
    file_opts.cookies = "C:/cookies/cookies.txt"
    file_only = downloader.build_yt_dlp_options(file_opts, lambda _data: None)
    assert file_only["cookiefile"] == "C:/cookies/cookies.txt"

    both_opts = _options()
    both_opts.cookies = "C:/cookies/cookies.txt"
    both_opts.cookies_from_browser = ("chrome", None, None, None)
    both = downloader.build_yt_dlp_options(both_opts, lambda _data: None)
    assert both["cookiesfrombrowser"] == ("chrome", None, None, None)
    assert "cookiefile" not in both
