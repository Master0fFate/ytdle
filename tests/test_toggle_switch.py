from PySide6.QtCore import Qt

from ui.components.toggle_switch import ToggleSwitch


def test_toggle_switch_is_compact_keyboard_accessible_and_animated(qtbot):
    switch = ToggleSwitch("Async mode")
    qtbot.addWidget(switch)
    switch.show()

    assert switch.sizeHint().height() == 22
    assert not switch.isChecked()

    qtbot.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert switch.isChecked()
    qtbot.waitUntil(lambda: switch.handlePosition > 0.99, timeout=500)

    switch.setFocus()
    qtbot.keyClick(switch, Qt.Key.Key_Space)
    assert not switch.isChecked()
    qtbot.waitUntil(lambda: switch.handlePosition < 0.01, timeout=500)
