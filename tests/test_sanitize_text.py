from app.utils.sanitize_text import sanitize_text


def test_sanitize_text_removes_html_and_scripts():
    raw = "  <div>Hello\n\n<script>alert('x')</script><p>World</p>   "
    cleaned = sanitize_text(raw)
    assert "<script" not in cleaned
    assert "<div" not in cleaned
    assert "Hello" in cleaned
    assert "World" in cleaned
    # No excessive whitespace
    assert "  " not in cleaned


def test_sanitize_text_handles_empty():
    assert sanitize_text("") == ""


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

def test_sanitize_text_handles_whitespace_only():
    """Input containing only whitespace returns an empty string."""
    assert sanitize_text("   \t\n  ") == ""


def test_sanitize_text_strips_deeply_nested_html():
    """Deeply nested HTML tags are stripped and inner text is preserved."""
    raw = '<div><p><span><b>Deep content</b></span></p></div>'
    cleaned = sanitize_text(raw)
    assert '<div' not in cleaned
    assert '<span' not in cleaned
    assert 'Deep content' in cleaned


def test_sanitize_text_strips_script_preserves_text():
    """Script tags are stripped but surrounding text is preserved."""
    raw = 'Before<script>evil()</script>After'
    cleaned = sanitize_text(raw)
    assert '<script' not in cleaned
    assert 'Before' in cleaned
    assert 'After' in cleaned


def test_sanitize_text_no_html_passthrough():
    """No HTML tags survive sanitization — output is plain text only."""
    raw = '<h1>Title</h1><p>Paragraph with <em>emphasis</em>.</p>'
    cleaned = sanitize_text(raw)
    assert '<' not in cleaned
    assert '>' not in cleaned
