# Product

## Register

product

## Users

YTDLE is for Windows-first users who want a focused desktop downloader for videos, playlists, audio extraction, and authenticated/cookie-assisted downloads without needing to remember yt-dlp command lines. Users may be casual downloaders, creators archiving their own media, or power users batching many links.

## Product Purpose

YTDLE wraps yt-dlp, FFmpeg, and optional aria2c acceleration in a reliable GUI and CLI. Success means a user can paste links, choose the output folder and format, understand which toolchain is available, start downloads confidently, recover from failures, and inspect history without leaving the app.

## Brand Personality

Precise, calm, capable. The interface should feel like a polished utility: direct labels, clear state, visible diagnostics, no decorative noise.

## Anti-references

Avoid generic dark-card dashboards, vague "magic downloader" copy, hidden dependency failures, tiny low-contrast controls, and workflows that require users to debug FFmpeg or aria2c from a terminal.

## Design Principles

- Make readiness visible before the user commits to a download.
- Keep expert controls available without making the first-run path feel crowded.
- Prefer specific diagnostics over generic failure messages.
- Preserve momentum: paste links, choose format, download, open output.
- Treat local binaries and history data as user-owned operational state.

## Accessibility & Inclusion

Aim for readable dark-mode contrast, keyboard shortcuts for primary flows, clear focus states, text labels that do not rely on color alone, and reduced cognitive load for users who do not know the underlying tools.
