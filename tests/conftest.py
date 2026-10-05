import pytest

from ui.skins import DEFAULT_SKIN, active_skin, set_active_skin


@pytest.fixture(autouse=True)
def _reset_skin():
    """Skins are process-wide; never let one test's choice leak into the next."""
    yield
    if active_skin().key == DEFAULT_SKIN:
        return
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        set_active_skin(DEFAULT_SKIN)
        return
    from ui.styles import apply_chrome

    apply_chrome(app, DEFAULT_SKIN)
