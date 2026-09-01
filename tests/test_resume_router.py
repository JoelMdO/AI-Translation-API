import pytest

import app.utils.summary.summary_article as sa
import app.services.summary as ss  # patch build_context_block in the module where it is used

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

AUTH = {"Authorization": "Bearer devtoken"}
VALID_PAYLOAD = {"title": "Sample", "body": "Long article body", "language": "en"}


async def _fake_resume(title, body, model, language, context_block=""): #type: ignore
    return "Generated summary of article."


async def _no_context(title, language): #type: ignore
    return ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summary_endpoint_returns_article(async_client, monkeypatch): #type: ignore
    """Baseline: /api/summary returns 200 with success=True and article text."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await async_client.post('/api/summary', json=VALID_PAYLOAD, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert data.get('success') is True #type: ignore
    assert 'generated summary' in data.get('article', '').lower() #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_with_html_body(async_client, monkeypatch): #type: ignore
    """HTML body in request is accepted and returns 200 with success=True."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    payload = {"title": "<b>Article</b>", "body": "<p>HTML body content</p>", "language": "en"}
    resp = await async_client.post('/api/summary', json=payload, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert data.get('success') is True #type: ignore
    assert 'article' in data


@pytest.mark.asyncio
async def test_summary_endpoint_response_shape(async_client, monkeypatch): #type: ignore
    """Response JSON must contain both `article` and `success` keys."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await async_client.post('/api/summary', json=VALID_PAYLOAD, headers=AUTH) #type: ignore

    data = resp.json() #type: ignore
    assert 'article' in data
    assert 'success' in data


@pytest.mark.asyncio
async def test_summary_endpoint_422_missing_required_fields(async_client): #type: ignore
    """Payload missing required `title` and `body` returns 422 Unprocessable Entity."""
    resp = await async_client.post('/api/summary', json={"language": "en"}, headers=AUTH) #type: ignore

    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_403_without_auth_header(async_client): #type: ignore
    """Request without Authorization header returns 403 Forbidden."""
    resp = await async_client.post('/api/summary', json=VALID_PAYLOAD) #type: ignore

    assert resp.status_code == 403 #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_service_error_returns_success_false(async_client, monkeypatch): #type: ignore
    """Model-level error is caught by the service; endpoint returns 200 with success=False."""
    async def failing_resume(title, body, model, language, context_block=""): #type: ignore
        raise Exception("Model timeout")

    monkeypatch.setattr(sa.summary_utils, 'resume_article', failing_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await async_client.post('/api/summary', json=VALID_PAYLOAD, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    assert resp.json().get('success') is False #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_article_is_non_empty_string(async_client, monkeypatch): #type: ignore
    """On success, `article` in the response must be a non-empty string."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    resp = await async_client.post('/api/summary', json=VALID_PAYLOAD, headers=AUTH) #type: ignore

    article = resp.json().get('article', '') #type: ignore
    assert isinstance(article, str) and len(article) > 0


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summary_endpoint_422_missing_only_title(async_client): #type: ignore
    """Payload with only `body` and `language` (no title) returns 422."""
    resp = await async_client.post('/api/summary', json={'body': 'Some body text.', 'language': 'en'}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_422_missing_only_body(async_client): #type: ignore
    """Payload with only `title` and `language` (no body) returns 422."""
    resp = await async_client.post('/api/summary', json={'title': 'A Title', 'language': 'en'}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_xss_in_body_does_not_crash(async_client, monkeypatch): #type: ignore
    """XSS injection in body is sanitized before reaching the model; endpoint returns 200."""
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    xss_payload = {
        'title': '<script>alert(1)</script>My Article',
        'body': '<img src=x onerror=alert(1)><p>Safe aviation content.</p>',
        'language': 'en',
    }
    resp = await async_client.post('/api/summary', json=xss_payload, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore


@pytest.mark.asyncio
async def test_summary_endpoint_wrong_method_get_returns_405(async_client): #type: ignore
    """GET /api/summary returns 405 Method Not Allowed."""
    resp = await async_client.get('/api/summary', headers=AUTH) #type: ignore
    assert resp.status_code == 405 #type: ignore
