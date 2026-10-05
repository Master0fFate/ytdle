"""Selectable looks for the desktop window.

A skin is a color set, interface type, a stylesheet, and a few presentation
choices that a stylesheet alone cannot make (icons or [words] for actions,
colored dots or text marks for state, and the switch drawing). The window
layout and behavior are the same in every skin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ui.themes import angelcore, default, material3

DEFAULT_SKIN = "default"

_DEFAULT_COLORS = {
    "bg": "#101018",
    "surface": "#191921",
    "container": "#25242e",
    "raised": "#302f3a",
    "field": "#1d1c26",
    "rule": "#494653",
    "outline": "#918d9c",
    "muted": "#aaa7b7",
    "text": "#e8e6f0",
    "strong": "#ffffff",
    "accent": "#7c3aed",
    "accent_end": "#a259f7",
    "accent_hover": "#8b50f4",
    "accent_pressed": "#6830cb",
    "accent_soft": "#231a38",
    "on_accent": "#ffffff",
    "primary_container": "#493177",
    "selected": "#493177",
    "on_selected": "#ffffff",
    "focus": "#bd9bff",
    "success": "#7fd4a3",
    "warning": "#f0c063",
    "error": "#f28b95",
    "icon": "#cac6d5",
    "icon_active": "#f0edf7",
    "icon_disabled": "#706d7b",
    "art_ink": "#bd9bff",
}

# Material 3 dark scheme, purple seed: tonal surfaces, a light primary with dark
# text, a secondary container for selection, and a single outline token.
_MATERIAL3_COLORS = {
    "bg": "#141218",
    "surface": "#1d1b20",
    "container": "#211f26",
    "raised": "#2b2930",
    "field": "#36343b",
    "rule": "#49454f",
    "outline": "#938f99",
    "muted": "#cac4d0",
    "text": "#e6e0e9",
    "strong": "#e6e0e9",
    "accent": "#d0bcff",
    "accent_end": "#d0bcff",
    "accent_hover": "#c2adf1",
    "accent_pressed": "#b49ee3",
    "accent_soft": "#2c2440",
    "on_accent": "#381e72",
    "primary_container": "#4f378b",
    "selected": "#4a4458",
    "on_selected": "#e8def8",
    "focus": "#d0bcff",
    "success": "#89d4a5",
    "warning": "#f0c063",
    "error": "#f2b8b5",
    "icon": "#cac4d0",
    "icon_active": "#e6e0e9",
    "icon_disabled": "#6c6773",
    "art_ink": "#d0bcff",
}

# Angelcore: one near-black field, neutral inks only. State is carried by
# words and marks ([ok], [!]), so success/warning/error stay neutral.
_ANGELCORE_COLORS = {
    "bg": "#090909",
    "surface": "#111111",
    "container": "#111111",
    "raised": "#191919",
    "field": "#090909",
    "rule": "#2b2b2b",
    "outline": "#737373",
    "muted": "#909090",
    "text": "#b8b8b8",
    "strong": "#eeeeee",
    "accent": "#eeeeee",
    "accent_end": "#eeeeee",
    "accent_hover": "#ffffff",
    "accent_pressed": "#b8b8b8",
    "accent_soft": "#191919",
    "on_accent": "#090909",
    "primary_container": "#191919",
    "selected": "#191919",
    "on_selected": "#eeeeee",
    "focus": "#eeeeee",
    "success": "#b8b8b8",
    "warning": "#eeeeee",
    "error": "#eeeeee",
    "icon": "#b8b8b8",
    "icon_active": "#eeeeee",
    "icon_disabled": "#5c5c5c",
    "art_ink": "#2a2a2a",
}


@dataclass(frozen=True)
class Skin:
    key: str
    name: str
    summary: str
    colors: dict
    fonts: tuple[str, ...]  # interface font, then fallbacks
    font_point_size: float
    stylesheet: Callable[[dict, str], str]
    icon_actions: bool = True      # False: actions read as [words]
    state_marks: bool = False      # True: [ok] / [!] marks instead of colored dots
    page_marker: bool = False      # True: "> " before the current page
    toggle_style: str = "switch"   # switch | material | marks
    brand_style: str = "gradient"  # gradient | tonal | mono
    empty_art: str = "glyph"       # glyph | dither


SKINS: dict[str, Skin] = {
    skin.key: skin
    for skin in (
        Skin(
            key="default",
            name="Default",
            summary="YTDLE's own look: soft purple, rounded, calm.",
            colors=_DEFAULT_COLORS,
            fonts=("Roboto", "Segoe UI"),
            font_point_size=10,
            stylesheet=default.build,
        ),
        Skin(
            key="material3",
            name="Material 3",
            summary="Google's Material 3 dark scheme: tonal surfaces, filled fields, tabs.",
            colors=_MATERIAL3_COLORS,
            fonts=("Roboto", "Segoe UI"),
            font_point_size=10,
            stylesheet=material3.build,
            toggle_style="material",
            brand_style="tonal",
        ),
        Skin(
            key="angelcore",
            name="Angelcore",
            summary="Near-black, square, monospace. Words instead of icons.",
            colors=_ANGELCORE_COLORS,
            fonts=("Cascadia Mono", "Consolas", "Courier New"),
            font_point_size=9.75,
            stylesheet=angelcore.build,
            icon_actions=False,
            state_marks=True,
            page_marker=True,
            toggle_style="marks",
            brand_style="mono",
            empty_art="dither",
        ),
    )
}

# The live color set. Widgets that paint themselves read it at paint time, so
# switching skins only needs a repaint, not a rebuilt window.
COLORS: dict = dict(_DEFAULT_COLORS)
_active = SKINS[DEFAULT_SKIN]


def resolve(key: object) -> Skin:
    """Return the skin for a saved key; unknown or empty keys fall back to Default."""
    return SKINS.get(str(key or ""), SKINS[DEFAULT_SKIN])


def active_skin() -> Skin:
    return _active


def set_active_skin(key: object) -> Skin:
    global _active
    _active = resolve(key)
    COLORS.clear()
    COLORS.update(_active.colors)
    return _active


STATE_MARKS = {
    "error": "[!]",
    "warning": "[!]",
    "done": "[ok]",
    "active": "...",
}


def state_color(state: str) -> str:
    return {
        "ready": COLORS["outline"],
        "pending": COLORS["outline"],
        "active": COLORS["focus"],
        "done": COLORS["success"],
        "warning": COLORS["warning"],
        "partial": COLORS["warning"],
        "notice": COLORS["warning"],
        "error": COLORS["error"],
    }.get(state, COLORS["outline"])
