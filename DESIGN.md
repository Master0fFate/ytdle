# YTDLE design system

## Direction

YTDLE is a dark, task-first desktop utility. It adapts **Material 3 Expressive** principles to PySide6/Qt Fusion widgets; it is not the Android Material component library. Keep the existing royal-purple accent (`#7c3aed`). Use shape, tonal surfaces, and one clear primary action for hierarchy—not bright frames around every component.

## Color, type, and shape

- Dark surface `#101018`, low container `#191921`, container `#25242e`, raised container `#302f3a`; white-on-dark text `#e8e6f0` and muted text `#aaa7b7`.
- Purple marks the download action, selected segment/tab, active switch, progress, and focus indicator. Disabled controls remain legible and muted.
- Bundle Roboto for interface type; keep Consolas/Cascadia Mono for the activity log. Ship its OFL license with the EXE.
- Inputs are filled **pills on both ends**, not white-outlined fields. Their quiet bottom line becomes purple when focused. Group containers use tonal fills without decorative borders. Buttons use circular or pill shapes with distinct primary size.
- Hover, pressed, focus, checked, and disabled states change color, not control geometry. Keyboard focus remains visible. Scrollbars use a quiet track and rounded tonal thumb with clearer hover/drag states.

## Controls and workflow

- Icon-only actions include a hover tooltip and accessible name. This applies to queue tools, history, network, transport, folder, and help actions. Keep the MP3/MP4 labels, form labels, switch labels, status words, and tab labels: icons alone cannot communicate those choices or results.
- Download is purple and the same 40 px hit target as adjacent transport actions. Secondary icon actions use the same circle size. Keep the MP3/MP4 selection joined, and keep switches keyboard-operable.
- Preserve Download/Cookies tabs, input validation, toolchain/network diagnostics, history, pause/resume/skip/cancel, and CLI behavior.
- Queue tools share the directory row. History and network share the transport row with download controls. The 48 px title bar contains its 40 px window buttons; History tabs leave 12 px before the table. At 760 × 560, the queue, format, actions, and bottom activity log must not overlap. The normal canvas is 920 × 620. Check both sizes and the Cookies/History views.
- The bottom log is a **bounded view** (last 1,500 lines); the file log and database history remain separate and persistent.

Screenshot: [dark desktop view](docs/screenshots/ytdle-material3-dark.png).
