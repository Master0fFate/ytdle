"""Small text helpers shared by the desktop UI."""

import html

from PySide6.QtCore import QLocale
from PySide6.QtGui import Qt


def count(value: int) -> str:
    """A whole number with the user's digit grouping: 1284 -> '1,284' (en-US)."""
    return QLocale().toString(int(value))


def plain_tip(text: str) -> str:
    """Tooltip text that always renders literally.

    Qt shows a tooltip as rich text when it looks like HTML, so a video titled
    '<b>Live</b>' would turn bold and lose its tags. Escape it in that case.
    """
    if not text or not Qt.mightBeRichText(text):
        return text
    return "<qt>" + html.escape(text).replace("\n", "<br>") + "</qt>"
