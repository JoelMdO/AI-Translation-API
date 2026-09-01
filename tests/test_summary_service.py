import pytest
from app.schemas.translation import ResumeRequest
from app.services.summary import summary_service

import app.utils.summary.summary_article as sa
import app.services.summary as ss  # patch build_context_block in the module where it is used

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

PLAIN_REQ = ResumeRequest(title="Sample Title", body="Long article body here.", language="en")
HTML_REQ  = ResumeRequest(title="<b>My Title</b>", body="<p>Article body content</p>", language="es")


async def _fake_resume(title, body, model, language, context_block=""): #type: ignore
    return "This is a short summary."


async def _no_context(title, language): #type: ignore
    return ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summary_service_returns_sanitized(monkeypatch):#type: ignore
    """Baseline: service returns success=True and article text on happy path."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert resp.success is True
    assert "short summary" in resp.article.lower()


@pytest.mark.asyncio
async def test_summary_service_html_body_is_sanitized(monkeypatch): #type: ignore
    """
    HTML content goes through sanitize_html before reaching the model.
    sanitize_html preserves safe tags but removes malicious content —
    the service must succeed and forward non-empty content to the model.
    """
    captured: dict = {} #type: ignore

    async def capture_resume(title, body, model, language, context_block=""): #type: ignore
        captured['title'] = title
        captured['body'] = body
        return "Summary from HTML article."

    monkeypatch.setattr(sa.summary_utils, 'resume_article', capture_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(HTML_REQ)

    assert resp.success is True
    # Sanitizer preserves safe tags; content must be non-empty and reach the model
    assert len(captured.get('title', '')) > 0 #type: ignore
    assert len(captured.get('body', '')) > 0 #type: ignore
    # Script/event-handler injection must be absent
    assert '<script>' not in captured.get('title', '') #type: ignore
    assert 'onerror' not in captured.get('body', '') #type: ignore


@pytest.mark.asyncio
async def test_summary_service_returns_success_false_on_error(monkeypatch): #type: ignore
    """When the model call raises, service catches the error and returns success=False."""
    async def failing_resume(title, body, model, language, context_block=""): #type: ignore
        raise RuntimeError("Ollama timeout")

    monkeypatch.setattr(sa.summary_utils, 'resume_article', failing_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert resp.success is False


@pytest.mark.asyncio
async def test_summary_service_response_has_required_fields(monkeypatch): #type: ignore
    """Response always exposes `article` and `success` attributes."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert hasattr(resp, 'article')
    assert hasattr(resp, 'success')


@pytest.mark.asyncio
async def test_summary_service_article_is_non_empty_on_success(monkeypatch): #type: ignore
    """On success, `article` must be a non-empty string."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert isinstance(resp.article, str)
    assert len(resp.article.strip()) > 0


@pytest.mark.asyncio
async def test_summary_service_language_forwarded_to_model(monkeypatch): #type: ignore
    """The `language` from the request is forwarded to the model call."""
    captured_lang: dict = {} #type: ignore
 
    async def capture_lang(title, body, model, language, context_block=""): #type: ignore
        captured_lang['language'] = language
        return "Summary."

    monkeypatch.setattr(sa.summary_utils, 'resume_article', capture_lang) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    req = ResumeRequest(title="T", body="B", language="fr")
    await summary_service.summarize(req)

    assert captured_lang.get('language') == 'fr' #type: ignore


@pytest.mark.asyncio
async def test_summary_service_error_article_contains_message(monkeypatch): #type: ignore
    """On failure the `article` field describes the error and is not empty."""
    async def failing_resume(title, body, model, language, context_block=""): #type: ignore
        raise ValueError("unexpected input")

    monkeypatch.setattr(sa.summary_utils, 'resume_article', failing_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert resp.success is False
    assert len(resp.article) > 0


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summary_service_model_returns_empty_string_handled_gracefully(monkeypatch): #type: ignore
    """When the model returns an empty string, the service must not crash."""
    async def empty_resume(title, body, model, language, context_block=""): #type: ignore
        return ""

    monkeypatch.setattr(sa.summary_utils, 'resume_article', empty_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    # Must not raise; success may be True or False but article must be a string
    assert isinstance(resp.article, str)
    assert hasattr(resp, 'success')


@pytest.mark.asyncio
async def test_summary_service_xss_in_title_stripped_before_model(monkeypatch): #type: ignore
    """
    XSS injection in title is sanitized before being forwarded to the model.
    The captured title passed to resume_article must not contain raw script tags.
    """
    captured: dict = {} #type: ignore

    async def capture_resume(title, body, model, language, context_block=""): #type: ignore
        captured['title'] = title
        captured['body'] = body
        return "Clean summary."

    monkeypatch.setattr(sa.summary_utils, 'resume_article', capture_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    xss_req = ResumeRequest(
        title='<script>alert("xss")</script>Safe Title',
        body='<img src=x onerror=alert(1)><p>Safe body content.</p>',
        language='en',
    )
    resp = await summary_service.summarize(xss_req)

    assert resp.success is True
    assert '<script>' not in captured.get('title', '') #type: ignore
    assert 'onerror' not in captured.get('body', '').lower() #type: ignore
    assert 'javascript:' not in captured.get('title', '').lower() #type: ignore


@pytest.mark.asyncio
async def test_summary_service_model_raises_value_error_returns_success_false(monkeypatch): #type: ignore
    """ValueError from the model is caught; service returns success=False."""
    async def value_error_resume(title, body, model, language, context_block=""): #type: ignore
        raise ValueError("Invalid model input")

    monkeypatch.setattr(sa.summary_utils, 'resume_article', value_error_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await summary_service.summarize(PLAIN_REQ)

    assert resp.success is False
