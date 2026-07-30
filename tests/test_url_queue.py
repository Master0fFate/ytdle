from ui.url_queue import analyze_url_queue, merge_url_queue


def test_analyze_url_queue_preserves_order_and_reports_cleanup_items():
    analysis = analyze_url_queue(
        "\ufeffhttps://example.com/one\n"
        "# Exported retry list\n"
        " https://example.com/two \n"
        "https://example.com/one\n"
        "not a link\n"
        "https://bad host/video\n"
    )

    assert analysis.urls == (
        "https://example.com/one",
        "https://example.com/two",
    )
    assert analysis.duplicate_count == 1
    assert analysis.comment_count == 1
    assert [entry.line_number for entry in analysis.invalid_entries] == [5, 6]
    assert analysis.cleaned_text == ("https://example.com/one\nhttps://example.com/two")
    assert analysis.has_cleanup_items


def test_analyze_url_queue_explains_common_malformed_entries():
    analysis = analyze_url_queue(
        "ftp://example.com/video\n"
        "https:///missing-host\n"
        "https://example.com:invalid-port/video\n"
    )

    assert [entry.reason for entry in analysis.invalid_entries] == [
        "must start with http:// or https://",
        "is missing a website host",
        "is malformed",
    ]


def test_analyze_url_queue_handles_ipv6_credentials_unicode_and_bom():
    analysis = analyze_url_queue(
        "\ufeffhttps://例え.テスト/路径\n"
        "https://[2001:db8::1]:8443/video\n"
        "https://user:pass@example.com/private\n"
        "https://[2001:db8::1]:8443/video\n"
        "https://example.com:99999/video\n"
        "https://[2001:db8::1/video\n"
        "https://example.com/path\u2003segment\n"
        "\ufeffhttps://example.com/not-first-bom\n"
        "   # ignored comment\n"
    )

    assert analysis.urls == (
        "https://例え.テスト/路径",
        "https://[2001:db8::1]:8443/video",
        "https://user:pass@example.com/private",
    )
    assert analysis.duplicate_count == 1
    assert analysis.comment_count == 1
    assert [entry.line_number for entry in analysis.invalid_entries] == [5, 6, 7, 8]
    assert [entry.reason for entry in analysis.invalid_entries] == [
        "is malformed",
        "is malformed",
        "contains spaces",
        "must start with http:// or https://",
    ]


def test_merge_url_queue_adds_only_new_valid_links_and_preserves_editor_text():
    existing = (
        "https://example.com/one\nleave this line for the user\nhttps://example.com/one"
    )

    result = merge_url_queue(
        existing,
        (
            "# Generated list\n"
            "https://example.com/one\n"
            "https://example.com/two\n"
            "https://example.com/two\n"
            "mailto:user@example.com",
        ),
    )

    assert result.added_urls == ("https://example.com/two",)
    assert result.duplicate_count == 2
    assert result.comment_count == 1
    assert len(result.invalid_entries) == 1
    assert result.text == f"{existing}\nhttps://example.com/two"
