"""Stylesheet builders, one module per skin. Each exposes build(colors, arrow_path)."""

_STATES = ("ready", "pending", "active", "done", "warning", "partial", "notice", "error")


def state_color(c: dict, state: str) -> str:
    if state == "active":
        return c["focus"]
    if state == "done":
        return c["success"]
    if state in ("warning", "partial", "notice"):
        return c["warning"]
    if state == "error":
        return c["error"]
    return c["outline"]


def state_rules(c: dict, selector: str, prop: str) -> str:
    return "\n".join(
        f'{selector}[state="{state}"] {{ {prop}: {state_color(c, state)}; }}'
        for state in _STATES
    )


def combo_arrow(arrow_path: str) -> str:
    if not arrow_path:
        return ""
    return f"QComboBox::down-arrow {{ image: url({arrow_path}); width: 12px; height: 12px; }}"
