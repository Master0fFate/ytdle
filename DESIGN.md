# YTDLE Design System

## Direction

YTDLE is an **Operate** surface: compact, calm, and task-first. Its visual language follows Angelcore reference-monochrome for a hard-edged desktop workspace, not a dashboard and not a fake terminal.

## Visual Rules

- Near-black field (`#090909`) with square corners (`border-radius: 0`) and dim `#2b2b2b` hairlines. Do not cage every control in a light-gray box.
- Interface type is mono: Consolas / Cascadia Mono / Courier New.
- Royal purple (`#7c3aed`) is the only hue accent, as a documented exception to reference-monochrome.
- Reserve purple for the primary action, focus, selected tab, progress chunk, and enabled switches.
- Do not use decorative background images, dither wallpaper, gradients, glows, glass, or tinted card stacks.
- Status information belongs in the activity console as words (`[ok]`, `[!]`, Ready), not color-only dots.

## Components

- Inputs and secondary buttons use compact 22–26 px visual heights.
- MP3/MP4 is one joined segmented control, never two detached buttons.
- Binary settings use compact square switches.
- Tool buttons use Google Material Icons Outlined, recolored to the mono ink scale.
- Hover, focus, pressed, checked, and disabled states must not change layout geometry.

## Layout

- Preserve the Download and Cookies workflow and all existing controls.
- Utility actions and download transport controls occupy separate rows so narrow windows cannot collide.
- The default canvas is 920 × 700 logical pixels; 760 × 600 remains usable without overlap.
- Toolchain, network, readiness, progress notes, and errors flow into the bottom console.

## Typography

Use Consolas / Cascadia Mono / Courier New for interface text and the activity console.
