from app.utils.sanitize_html import sanitize_html


def test_sanitize_html_removes_scripts_and_event_handlers():
    raw = '<div onclick="doEvil()"><script>evil()</script><a href="javascript:bad()">link</a><p>Safe</p></div>'
    cleaned = sanitize_html(raw)
    assert '<script' not in cleaned
    assert 'onclick' not in cleaned.lower()
    assert 'javascript:' not in cleaned.lower()
    assert '<p>Safe</p>' in cleaned


def test_sanitize_html_keeps_safe_structure():
    # <section> is not in the allowlist; only allowed tags must pass through unchanged.
    raw = '<div><h1>Title</h1><p>Text</p></div>'
    assert sanitize_html(raw) == raw


def test_sanitize_html_strips_disallowed_tags_preserves_content():
    # <section> and <article> are not in the allowlist — tags are stripped, content preserved.
    raw = '<section><h1>Title</h1><p>Text</p></section>'
    cleaned = sanitize_html(raw)
    assert '<section' not in cleaned
    assert '<h1>Title</h1>' in cleaned
    assert '<p>Text</p>' in cleaned


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

def test_sanitize_html_strips_img_onerror_handler():
    """img onerror event handler is removed."""
    raw = '<p>Safe</p><img src="x" onerror="alert(1)" />'
    cleaned = sanitize_html(raw)
    assert 'onerror' not in cleaned.lower()
    assert '<p>Safe</p>' in cleaned


def test_sanitize_html_strips_iframe():
    """iframe elements are removed entirely."""
    raw = '<p>Content</p><iframe src="https://evil.example.com"></iframe>'
    cleaned = sanitize_html(raw)
    assert '<iframe' not in cleaned.lower()
    assert '<p>Content</p>' in cleaned


def test_sanitize_html_strips_data_uri_in_src():
    """data: URIs in src attributes are stripped (potential XSS vector)."""
    raw = '<img src="data:text/html,<script>evil()</script>" />'
    cleaned = sanitize_html(raw)
    assert 'data:text/html' not in cleaned
    assert '<script>' not in cleaned


def test_sanitize_html_handles_empty_string():
    """Empty string input returns empty string without raising."""
    assert sanitize_html('') == ''


def test_sanitize_html_strips_nested_script_in_attribute():
    """Nested XSS attempt via style attribute is defused."""
    raw = '<p style="background:url(javascript:alert(1))">Text</p>'
    cleaned = sanitize_html(raw)
    assert 'javascript:' not in cleaned.lower()
