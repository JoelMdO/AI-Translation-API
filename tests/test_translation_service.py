import pytest

from app.schemas.translation import TranslationRequest, TranslationResponse, TranslatedText
from app.services.translation_service import TranslationService
import app.utils.translation.translate_html_content as thc

PLAIN_REQ = TranslationRequest(
    title="Hello",
    body="Some body text.",
    section="Intro section",
    target_language="Spanish",
    model="test-model",
)

HTML_REQ = TranslationRequest(
    title="<b>Hello</b>",
    body="<p>Body paragraph</p>",
    section="<em>Intro</em>",
    target_language="Spanish",
    model="test-model",
)


@pytest.mark.asyncio
async def test_translation_service_plain_text_path(monkeypatch):
    async def fake_plain_text(*args, **kwargs):
        return "Titulo Traducido"

    monkeypatch.setattr(thc.translateHTMLContent, "translate_plain_text", fake_plain_text)

    service = TranslationService()
    response = await service.translate(PLAIN_REQ)

    assert response.status == 200
    assert response.model_used == "test-model"
    assert response.translated_text.title == "Titulo Traducido"
    assert response.translated_text.body == "Titulo Traducido"
    assert response.translated_text.section == "Titulo Traducido"


@pytest.mark.asyncio
async def test_translation_service_html_path(monkeypatch):
    async def fake_html(*args, **kwargs):
        return "HTML traducido"

    monkeypatch.setattr(thc.translateHTMLContent, "translate_html_content", fake_html)

    service = TranslationService()
    response = await service.translate(HTML_REQ)

    assert response.status == 200
    assert isinstance(response.translated_text, TranslatedText)
    assert response.translated_text.title == "HTML traducido"
    assert response.translated_text.body == "HTML traducido"
    assert response.translated_text.section == "HTML traducido"


@pytest.mark.asyncio
async def test_translation_service_handles_translation_errors(monkeypatch):
    async def fake_plain_text(*args, **kwargs):
        raise RuntimeError("Ollama unreachable")

    monkeypatch.setattr(thc.translateHTMLContent, "translate_plain_text", fake_plain_text)

    service = TranslationService()
    response = await service.translate(PLAIN_REQ)

    assert response.status == 500
    assert response.translated_text.title == ""
    assert response.translated_text.body == ""
    assert response.translated_text.section == ""


@pytest.mark.asyncio
async def test_translation_service_keeps_required_fields(monkeypatch):
    async def fake_plain_text(*args, **kwargs):
        return "Resultado"

    monkeypatch.setattr(thc.translateHTMLContent, "translate_plain_text", fake_plain_text)

    service = TranslationService()
    response = await service.translate(PLAIN_REQ)

    for key in ("title", "body", "section"):
        assert key in response.translated_text.model_dump()
