"""Apply a skin to the application: fonts, the Fusion palette, and the stylesheet.

Skins are defined in ``ui.skins``; their stylesheets live in ``ui.themes``.
``COLORS`` is the live color set of the active skin.
"""

from ui.skins import COLORS, DEFAULT_SKIN, active_skin, set_active_skin

__all__ = ["COLORS", "apply_chrome", "strip_native_frames"]


def strip_native_frames(root) -> None:
    """Prevent Windows bevels from painting over Qt-styled controls."""
    from PySide6.QtWidgets import QFrame, QLineEdit, QPlainTextEdit, QTextBrowser

    for widget in root.findChildren(QLineEdit):
        widget.setFrame(False)
    for widget in root.findChildren(QPlainTextEdit):
        widget.setFrameStyle(QFrame.Shape.NoFrame)
    for widget in root.findChildren(QTextBrowser):
        widget.setFrameStyle(QFrame.Shape.NoFrame)


def _write_combo_arrow(color: str) -> str:
    """Render the combo chevron once per color; QSS needs a file URL for subcontrol images."""
    import tempfile
    from pathlib import Path

    from ui.icons import icon_pixmap

    target = Path(tempfile.gettempdir()) / "ytdle-ui" / f"chevron-{color.lstrip('#')}.png"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() and not icon_pixmap("chevron", 24, color, scale=1.0).save(
            str(target), "PNG"
        ):
            return ""
    except OSError:
        return ""
    return target.as_posix()


_FONT_LOADED = False


def _load_bundled_font() -> None:
    global _FONT_LOADED
    if _FONT_LOADED:
        return
    import sys
    from pathlib import Path

    from PySide6.QtGui import QFontDatabase

    font_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    font_path = font_root / "assets" / "Roboto.ttf"
    if font_path.is_file():
        QFontDatabase.addApplicationFont(str(font_path))
    _FONT_LOADED = True


def apply_chrome(app, skin: str = DEFAULT_SKIN) -> None:
    """Apply a skin's palette, font, and stylesheet to native popups and widgets."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QPalette

    current = set_active_skin(skin)
    _load_bundled_font()
    font = QFont()
    font.setFamilies(list(current.fonts))
    font.setPointSizeF(current.font_point_size)
    app.setFont(font)
    app.setStyle("Fusion")
    # Ask Windows for dark native frames on dialogs and message boxes too.
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(Qt.ColorScheme.Dark)

    c = COLORS
    palette = app.palette()
    # Light/Midlight/Mid stay dark: Fusion paints bevels from them.
    ink = {
        QPalette.ColorRole.Window: c["bg"],
        QPalette.ColorRole.Base: c["field"],
        QPalette.ColorRole.AlternateBase: c["container"],
        QPalette.ColorRole.Button: c["container"],
        QPalette.ColorRole.ButtonText: c["text"],
        QPalette.ColorRole.WindowText: c["text"],
        QPalette.ColorRole.Text: c["text"],
        QPalette.ColorRole.PlaceholderText: c["muted"],
        QPalette.ColorRole.BrightText: c["strong"],
        QPalette.ColorRole.Light: c["raised"],
        QPalette.ColorRole.Midlight: c["container"],
        QPalette.ColorRole.Mid: c["rule"],
        QPalette.ColorRole.Dark: c["bg"],
        QPalette.ColorRole.Shadow: c["bg"],
        QPalette.ColorRole.Highlight: c["primary_container"],
        QPalette.ColorRole.HighlightedText: c["strong"],
        QPalette.ColorRole.ToolTipBase: c["raised"],
        QPalette.ColorRole.ToolTipText: c["text"],
        QPalette.ColorRole.Link: c["focus"],
    }
    for role, color in ink.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(current.stylesheet(c, _write_combo_arrow(c["muted"])))


def current_skin_key() -> str:
    return active_skin().key
