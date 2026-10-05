# YTDLE design system

## Direction

YTDLE is a dark, task-first desktop utility. It adapts **Material 3 Expressive** principles to PySide6/Qt Fusion widgets; it is not the Android Material component library. Keep the royal-purple accent (`#7c3aed`). Use shape, tonal surfaces, and one clear primary action for hierarchy, not bright frames around every component.

The main page answers three questions in reading order: **what** (links), **how** (format, quality, folder), and **what is happening** (status card, activity). Everything else lives on the Options and Cookies pages.

## Skins

The layout and behavior are shared; a skin (`ui/skins.py`, stylesheets in `ui/themes/`) supplies colors, fonts, a stylesheet, and the few choices a stylesheet cannot make: icons or `[words]` for actions, colored dots or `[ok]`/`[!]` marks for state, the switch drawing, the brand mark, and the empty-state art. Widgets that paint themselves read the live `COLORS` at paint time, so switching is a repaint, not a rebuild. The choice is saved as `skin` in settings; unknown values fall back to Default.

| Skin | Character | Rules that must hold |
| --- | --- | --- |
| Default | YTDLE's own soft purple, rounded | Described in the sections below. |
| Material 3 | Google's M3 dark scheme | Filled text fields (4 px top corners, indicator line), primary tabs with a 3 px underline, filled primary button with on-primary text, outlined segmented buttons with a secondary-container selection, tonal secondary buttons, 12 px cards, the 52 × 32 switch, a 4 px linear indicator, inverse tooltips. |
| Angelcore | Reference-monochrome profile | Zero radius everywhere; neutral inks only (no hue, no gradient); one mono family; regions split by one hairline, no boxed controls; fields carry one bottom rule; hover is a surface change, focus a 2 px outline; the only fill is Download; state in words and marks; ambient art is a fixed 4 × 4 ordered dither of YTDLE's own glyph. `tests/test_skins.py` enforces the radius, hue, and gradient rules. |

Accessible names, labels, and shortcuts never change with the skin. Check every skin at 760 × 480, 760 × 560, and 920 × 640 (`tests/test_skins.py`), and look at it in the dev UI lab with worst-case data (`python -m dev.ui_lab --data worst --skin <key>`).

## Color, type, and shape (Default)

- Dark surface `#101018`, low container `#191921`, container `#25242e`, raised container `#302f3a`; text `#e8e6f0` and muted text `#aaa7b7`.
- Purple marks the Download action (a left-to-right gradient to `#a259f7`), selected nav/segments, active switches, progress, and focus. States use soft semantic colors: success `#7fd4a3`, warning `#f0c063`, error `#f28b95`. Color is never the only signal: every state dot or chip has a word next to it.
- Bundle Roboto for interface type; keep Consolas/Cascadia Mono for the log. Ship its OFL license with the EXE.
- Inputs are filled **pills**, not outlined fields. Their quiet bottom line turns purple on focus. Disabled fields keep their fill and lose only the underline and text contrast, so they stay visible on the window and inside cards.
- Cards (`#191921`, 20 px radius) group content without borders. The link drop zone is the one dashed outline: dashed when empty, solid tint when focused, accent-dashed with a purple wash while a drag hovers.
- Hover, pressed, focus, checked, and disabled states change color, not geometry. Keyboard focus is always visible.

## Layout

- **Title bar (52 px)**: brand mark, `Download · Options · Cookies` nav pill, then network chip, network re-check, history, minimize, close. Drag uses the system move, so Windows snap works; double-click maximizes. A size grip sits in the bottom-right corner.
- **Download page**, top to bottom:
  1. Drop zone: "Links" title, link-count chip (warning color when invalid lines exist), `Paste` (labeled), import, clean, clear. The empty state is a centered link glyph, a one-line instruction, and shortcuts; clicks pass through to the editor.
  2. Format row: joined `MP3 | MP4` segments with glyphs, quality combo, "Whole playlist" switch.
  3. "Save to" row: folder field, choose-folder, open-folder.
  4. Action card: state dot, one-line headline, one-line detail (both elide; full text on hover), and the primary action. Idle shows **Download** (labeled, 42 px, at least 132 px wide, "Download N" for N > 1). A running batch swaps it for pause, skip, and a labeled **Stop**. A 6 px gradient progress bar spans the card and never moves backward within a batch.
  5. Activity card: `Downloads | Log` segments. Downloads shows one row per link: dot, short link, detail line (saved path or failure reason), and a state word (Waiting, Downloading, Saved, Failed, Skipped, Not started).
- **Options page**: Skin, File names, FFmpeg arguments, Speed, Toolchain cards. **Cookies page**: Cookie source and Cookie file cards. Both scroll at small heights.
- The normal canvas is 920 × 640 and the minimum is 760 × 560; on small or high-DPI screens the minimum height follows the screen down to 480. At all three heights the five download-page rows must stay in order with no overlap. While a batch runs (and until the link list changes) the activity card gets most of the height.
- Long text shortens where the meaning is: paths, links, and the plan line in the middle (both ends survive), headlines at the end. Full text is always one hover away, and tooltips never render titles as HTML.

## Copy and feedback

- The idle detail line is a plan: `3 links · MP3 320k · to C:\Downloads`. Validation errors show in the card (headline and fix), never in a modal dialog, and focus moves to the field that needs the fix.
- Finished batches say what happened in words: "All 3 downloads saved", "2 saved, 1 failed", "Stopped. Nothing was saved."
- Icon-only actions have a tooltip and an accessible name. Destructive or batch actions in History (`Clear completed`, `Clear failed`, `Export failed`, `Retry failed`) carry words.
- The log is a **bounded view** (last 1,500 lines). The file log and database history are separate and persistent.

Screenshot: [dark desktop view](docs/screenshots/ytdle-material3-dark.png).
