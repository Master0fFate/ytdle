from PySide6.QtCore import QLocale

from ui.text import count, plain_tip


def test_counts_use_the_locale_digit_grouping():
    previous = QLocale()
    QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
    try:
        assert count(1284) == "1,284"
        assert count(7) == "7"
    finally:
        QLocale.setDefault(previous)


def test_tooltips_never_render_titles_as_html():
    assert plain_tip("Plain title") == "Plain title"
    assert plain_tip("<3 my cat") == "<3 my cat"
    assert plain_tip("<b>Live</b> & more") == "<qt>&lt;b&gt;Live&lt;/b&gt; &amp; more</qt>"
