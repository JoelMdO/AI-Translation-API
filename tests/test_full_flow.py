"""
Full-flow integration tests: translate → summarize pipeline.

These tests exercise the complete HTTP stack for both endpoints in sequence,
mocking only the external Ollama calls. Auth is bypassed via DEV_MODE=true
(set in conftest.py).
"""
import pytest

import app.utils.translation.translate_html_content as thc
import app.utils.summary.summary_article as sa
import app.services.summary as ss

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUTH = {"Authorization": "Bearer devtoken"}

ARTICLE_PLAIN = {
    "title": "AI transforms the world",
    "body": "Artificial intelligence is transforming technology at an unprecedented pace.",
    "section": "Technology",
    "target_language": "Spanish",
    "model": "test-model",
}

ARTICLE_HTML = {
    "title": "<b>AI transforms the world</b>",
    "body": "<p>Artificial intelligence is <em>transforming</em> technology.</p>",
    "section": "<strong>Technology</strong>",
    "target_language": "Spanish",
    "model": "test-model",
}


# ---------------------------------------------------------------------------
# Fake Ollama responses
# ---------------------------------------------------------------------------

async def _fake_translate_raw(text, title, body, section, target_language): #type: ignore
    return (
        "Título: Artículo de IA\n"
        "Cuerpo: La IA transforma el mundo\n"
        "Sección: Tecnología"
    )


async def _fake_translate_html(content, target_language): #type: ignore
    return f"[ES] {content}"


async def _fake_resume(title, body, model, language, context_block=""): #type: ignore
    return "Resumen: La IA está transformando el mundo de la tecnología."


async def _no_context(title, language): #type: ignore
    return ""


# ---------------------------------------------------------------------------
# Full-flow tests: plain-text article
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_flow_translate_then_summarize_plain_text(async_client, monkeypatch): #type: ignore
    """
    Step 1 — Translate a plain-text article via /api/translate.
    Step 2 — Summarize the translated content via /api/summary.
    Both calls return 200 with success=True.
    """
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_translate_raw) #type: ignore
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    # --- Step 1: translate ---
    translate_resp = await async_client.post('/api/translate', json=ARTICLE_PLAIN, headers=AUTH) #type: ignore
    assert translate_resp.status_code == 200 #type: ignore
    translated = translate_resp.json() #type: ignore
    assert translated["status"] == 200
    translated_title = translated['translated_text']['title'] #type: ignore
    translated_body  = translated['translated_text']['body'] #type: ignore
    assert len(translated_title) > 0 #type: ignore
    assert len(translated_body) > 0 #type: ignore

    # --- Step 2: summarize translated content ---
    summary_payload = { #type: ignore
        "title": translated_title,
        "body": translated_body,
        "language": "es",
    }
    summary_resp = await async_client.post('/api/summary', json=summary_payload, headers=AUTH) #type: ignore
    assert summary_resp.status_code == 200 #type: ignore
    summary = summary_resp.json() #type: ignore
    assert summary['success'] is True
    assert len(summary['article']) > 0 #type: ignore


@pytest.mark.asyncio
async def test_full_flow_translate_then_summarize_html_article(async_client, monkeypatch): #type: ignore
    """
    Same pipeline but with an HTML article body.
    HTML is sanitized at the summarize step; the final summary is plain text.
    """
    monkeypatch.setattr(thc.translateHTMLContent, "translate_html_content", _fake_translate_html) #type: ignore
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    # --- Step 1: translate HTML ---
    translate_resp = await async_client.post('/api/translate', json=ARTICLE_HTML, headers=AUTH) #type: ignore
    assert translate_resp.status_code == 200 #type: ignore
    translated = translate_resp.json() #type: ignore
    assert translated['success'] is True

    # --- Step 2: summarize ---
    summary_payload = { #type: ignore
        "title": translated['translated_text']['title'],
        "body": translated['translated_text']['body'],
        "language": "es",
    }
    summary_resp = await async_client.post('/api/summary', json=summary_payload, headers=AUTH) #type: ignore
    assert summary_resp.status_code == 200 #type: ignore
    assert summary_resp.json()['success'] is True #type: ignore


@pytest.mark.asyncio
async def test_full_flow_translate_failure_does_not_affect_summary(async_client, monkeypatch): #type: ignore
    """
    If translation fails (success=False), the client can still call /api/summary
    independently and get a valid response.
    """
    # Make translate fail
    async def failing_raw(text, title, body, section, target_language): #type: ignore
        raise RuntimeError("Translation model down")

    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", failing_raw) #type: ignore
    monkeypatch.setattr(sa.summary_utils, 'resume_article', _fake_resume) #type: ignore
    monkeypatch.setattr(ss, 'build_context_block', _no_context) #type: ignore

    # Translate should return success=False (service catches the error)
    translate_resp = await async_client.post('/api/translate', json=ARTICLE_PLAIN, headers=AUTH) #type: ignore
    assert translate_resp.status_code == 200 #type: ignore
    assert translate_resp.json()['success'] is False #type: ignore

    # Summary endpoint is independent — should still work
    summary_resp = await async_client.post( #type: ignore
        '/api/summary',
        json={"title": "Direct title", "body": "Direct body", "language": "en"},
        headers=AUTH,
    )
    assert summary_resp.status_code == 200 #type: ignore
    assert summary_resp.json()['success'] is True #type: ignore


@pytest.mark.asyncio
async def test_full_flow_both_endpoints_require_valid_request_body(async_client): #type: ignore
    """
    Both /api/translate and /api/summary validate their payloads and return 422
    when required fields are missing.
    """
    translate_resp = await async_client.post('/api/translate', json={}, headers=AUTH) #type: ignore
    assert translate_resp.status_code == 422 #type: ignore

    summary_resp = await async_client.post('/api/summary', json={}, headers=AUTH) #type: ignore
    assert summary_resp.status_code == 422 #type: ignore


@pytest.mark.asyncio
async def test_full_flow_both_endpoints_reject_unauthenticated_requests(async_client): #type: ignore
    """Both endpoints return 403 when no Authorization header is provided."""
    translate_resp = await async_client.post('/api/translate', json=ARTICLE_PLAIN) #type: ignore
    assert translate_resp.status_code == 403 #type: ignore

    summary_resp = await async_client.post( #type: ignore
        '/api/summary',
        json={"title": "T", "body": "B", "language": "en"},
    )
    assert summary_resp.status_code == 403 #type: ignore
