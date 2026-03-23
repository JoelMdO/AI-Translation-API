import pytest

import app.utils.translation.translate_html_content as thc

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

AUTH = {"Authorization": "Bearer devtoken"}
PLAIN_PAYLOAD = {
    "title": "Hello",
    "body": "Body text",
    "section": "Intro",
    "target_language": "Spanish",
    "model": "test-model",
}
HTML_PAYLOAD = {
    "title": "<b>Hello</b>",
    "body": "<p>Body paragraph</p>",
    "section": "<em>Intro</em>",
    "target_language": "Spanish",
    "model": "test-model",
}


async def _fake_raw(text, title, body, section, target_language): #type: ignore
    return "Título: Titulo Traducido\nCuerpo: Cuerpo Traducido\nSección: Sección Traducida"


async def _fake_html(content, target_language): #type: ignore
    return f"[translated] {content}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_translate_endpoint_returns_translated_json(async_client, monkeypatch): #type: ignore
    """Baseline: /api/translate returns 200 with success=True and all translated fields."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw) #type: ignore

    resp = await async_client.post('/api/translate', json=PLAIN_PAYLOAD, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert data.get('success') is True #type: ignore
    assert 'Titulo Traducido' in data.get('translated_text', {}).get('title', '') #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_html_body_returns_200(async_client, monkeypatch): #type: ignore
    """HTML body triggers per-field translation; endpoint still returns 200."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_html_content", _fake_html) #type: ignore

    resp = await async_client.post('/api/translate', json=HTML_PAYLOAD, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    assert resp.json().get('success') is True #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_response_contains_all_keys(async_client, monkeypatch): #type: ignore
    """translated_text in the response must have title, body and section."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw) #type: ignore

    resp = await async_client.post('/api/translate', json=PLAIN_PAYLOAD, headers=AUTH) #type: ignore

    translated = resp.json().get('translated_text', {}) #type: ignore
    for key in ("title", "body", "section"):
        assert key in translated, f"Missing key in translated_text: {key}"


@pytest.mark.asyncio
async def test_translate_endpoint_422_missing_required_fields(async_client): #type: ignore
    """Payload missing required fields returns 422 Unprocessable Entity."""
    resp = await async_client.post('/api/translate', json={}, headers=AUTH) #type: ignore

    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_403_without_auth_header(async_client): #type: ignore
    """Request without Authorization header returns 403 Forbidden."""
    resp = await async_client.post('/api/translate', json=PLAIN_PAYLOAD) #type: ignore

    assert resp.status_code == 403 #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_service_error_returns_success_false(async_client, monkeypatch): #type: ignore
    """Model-level error is caught by the service; endpoint returns 200 with success=False."""
    async def failing_raw(text, title, body, section, target_language): #type: ignore
        raise RuntimeError("Ollama unreachable")

    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", failing_raw) #type: ignore

    resp = await async_client.post('/api/translate', json=PLAIN_PAYLOAD, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore
    assert resp.json().get('success') is False #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_model_used_in_response(async_client, monkeypatch): #type: ignore
    """Response includes a non-empty `model_used` field."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw) #type: ignore

    resp = await async_client.post('/api/translate', json=PLAIN_PAYLOAD, headers=AUTH) #type: ignore

    data = resp.json() #type: ignore
    assert 'model_used' in data
    assert isinstance(data['model_used'], str) and len(data['model_used']) > 0 #type: ignore


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_translate_endpoint_422_missing_title(async_client): #type: ignore
    """Payload missing `title` returns 422."""
    payload = {k: v for k, v in PLAIN_PAYLOAD.items() if k != 'title'}
    resp = await async_client.post('/api/translate', json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_422_missing_section(async_client): #type: ignore
    """Payload missing `section` returns 422."""
    payload = {k: v for k, v in PLAIN_PAYLOAD.items() if k != 'section'}
    resp = await async_client.post('/api/translate', json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_xss_in_body_does_not_crash(async_client, monkeypatch): #type: ignore
    """XSS injection in body is sanitized by the service; endpoint returns 200 without crashing."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw) #type: ignore

    xss_payload = {
        **PLAIN_PAYLOAD,
        'body': '<script>alert("xss")</script><img src=x onerror=alert(1)>Safe content.',
        'title': '<a href="javascript:evil()">Title</a>',
    }
    resp = await async_client.post('/api/translate', json=xss_payload, headers=AUTH) #type: ignore

    assert resp.status_code == 200 #type: ignore


@pytest.mark.asyncio
async def test_translate_endpoint_wrong_method_get_returns_405(async_client): #type: ignore
    """GET /api/translate returns 405 Method Not Allowed."""
    resp = await async_client.get('/api/translate', headers=AUTH) #type: ignore
    assert resp.status_code == 405 #type: ignore #type: ignore
