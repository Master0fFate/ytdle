# YTDLE Design System

## Direction

YTDLE is an **Operate** surface: compact, calm, and task-first. Its visual language follows a restrained shadcn-style desktop system rather than a dashboard aesthetic.

## Visual Rules

- Use zinc-black neutral surfaces with crisp one-pixel borders.
- Royal purple (`#7c3aed`) is the only brand accent.
- Reserve purple for the primary action, focus, active tabs, progress, and enabled switches.
- Do not use decorative background images, gradients, glows, glass effects, or tinted card stacks.
- Semantic green, amber, and red are limited to real success, warning, and error output.
- Status information belongs in the activity console, not in separate banners.

## Components

- Inputs and secondary buttons use compact 28–30 px visual heights.
- MP3/MP4 is one joined segmented control, never two detached buttons.
- Binary settings use compact animated switches.
- Tool buttons use monochrome line icons rather than platform-colored icons.
- Corners stay between 5–8 px; only tiny badges and switch tracks may be pill-shaped.
- Hover, focus, pressed, checked, and disabled states must not change layout geometry.

## Layout

- Preserve the Download and Cookies workflow and all existing controls.
- Utility actions and download transport controls occupy separate rows so narrow windows cannot collide.
- The default canvas is 920 × 700 logical pixels; 760 × 600 remains usable without overlap.
- Toolchain, network, readiness, progress notes, and errors flow into the bottom console.

## Typography

Use Segoe UI Variable / Segoe UI for interface text and Cascadia Mono / Consolas only for the activity console.
