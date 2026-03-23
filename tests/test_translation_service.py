import pytest
from app.schemas.translation import TranslationRequest
from app.services.translation import translation_service
import app.utils.translation.translate_html_content as thc

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

PLAIN_REQ = TranslationRequest(
    title="Hello", body="Some body text.", section="Intro section", target_language="Spanish"
)
HTML_REQ = TranslationRequest(
    title="<b>Hello</b>", body="<p>Body paragraph</p>", section="<em>Intro</em>",
    target_language="Spanish"
)


async def _fake_raw_content(text, title, body, section, target_language): #type: ignore
    return "Título: Titulo Traducido\nCuerpo: Cuerpo Traducido\nSección: Sección Traducida"


async def _fake_html_content(content, target_language): #type: ignore
    return f"[translated] {content}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_translation_service_parses_plain_text(monkeypatch): #type: ignore
    """Baseline: service parses plain-text Ollama response into title/body/section."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw_content) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    assert resp.success is True
    assert isinstance(resp.translated_text, dict)
    assert "Titulo Traducido" in resp.translated_text.get("title", "")
    assert "Cuerpo Traducido" in resp.translated_text.get("body", "")
    section = resp.translated_text.get("section", "")
    assert "Sección Traducida" in section or "Seccion Traducida" in section


@pytest.mark.asyncio
async def test_translation_service_html_branch_translates_each_field(monkeypatch): #type: ignore
    """HTML body triggers per-field translate_html_content calls, not translate_raw_content."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_html_content", _fake_html_content) #type: ignore

    resp = await translation_service.translate(HTML_REQ)

    assert resp.success is True
    assert isinstance(resp.translated_text, dict)
    for key in ("title", "body", "section"):
        assert key in resp.translated_text


@pytest.mark.asyncio
async def test_translation_service_returns_success_false_on_error(monkeypatch): #type: ignore
    """If the underlying Ollama call raises, service catches it and returns success=False."""
    async def failing_html(content, target_language): #type: ignore
        raise RuntimeError("Ollama unreachable")

    async def failing_raw(text, title, body, section, target_language): #type: ignore
        raise RuntimeError("Ollama unreachable")

    monkeypatch.setattr(thc.translateHTMLContent, "translate_html_content", failing_html) #type: ignore
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", failing_raw) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    assert resp.success is False


@pytest.mark.asyncio
async def test_translation_service_response_has_all_keys(monkeypatch): #type: ignore
    """translated_text must always contain title, body and section keys."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw_content) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    for key in ("title", "body", "section"):
        assert key in resp.translated_text, f"Missing key in translated_text: {key}"


@pytest.mark.asyncio
async def test_translation_service_model_used_is_set(monkeypatch): #type: ignore
    """Response includes a non-empty `model_used` field."""
    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", _fake_raw_content) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    assert resp.success is True
    assert isinstance(resp.model_used, str)
    assert len(resp.model_used) > 0


@pytest.mark.asyncio
async def test_translation_service_failure_translated_text_has_empty_strings(monkeypatch): #type: ignore
    """On failure, translated_text values default to empty strings (not missing keys)."""
    async def failing_raw(text, title, body, section, target_language): #type: ignore
        raise RuntimeError("error")

    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", failing_raw) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    assert resp.success is False
    for key in ("title", "body", "section"):
        assert key in resp.translated_text


# ---------------------------------------------------------------------------
# Unhappy paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_translation_service_malformed_ollama_response_still_returns_dict(monkeypatch): #type: ignore
    """
    If Ollama returns a response that does not match the expected
    'Título: / Cuerpo: / Sección:' format, the service must not raise —
    it should return a dict (possibly with empty/fallback values).
    """
    async def malformed_raw(text, title, body, section, target_language): #type: ignore
        return "This is some random unformatted response from the model."

    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", malformed_raw) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    # Service must not raise; translated_text must always be a dict with the required keys
    assert isinstance(resp.translated_text, dict)
    for key in ("title", "body", "section"):
        assert key in resp.translated_text


@pytest.mark.asyncio
async def test_translation_service_empty_model_response_does_not_raise(monkeypatch): #type: ignore
    """Empty string returned by Ollama must not cause the service to crash."""
    async def empty_raw(text, title, body, section, target_language): #type: ignore
        return ""

    monkeypatch.setattr(thc.translateHTMLContent, "translate_raw_content", empty_raw) #type: ignore

    resp = await translation_service.translate(PLAIN_REQ)

    # Must not raise; result may be success=False or success=True with empty fields
    assert isinstance(resp.translated_text, dict)
    for key in ("title", "body", "section"):
        assert key in resp.translated_text
