import pytest
from app.schemas.translation import TranslationResponse, TranslatedText

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


@pytest.mark.asyncio
async def test_translate_endpoint_returns_200_and_translated_payload(async_client, monkeypatch):
    async def fake_translate(self, request):
        return TranslationResponse(
            translated_text=TranslatedText(
                title="Titulo Traducido",
                body="Cuerpo Traducido",
                section="Seccion Traducida",
            ),
            status=200,
            model_used="test-model",
        )

    monkeypatch.setattr("services.translation_service.TranslationService.translate", fake_translate)

    response = await async_client.post("/api/translate", json=PLAIN_PAYLOAD, headers=AUTH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == 200
    assert payload["model_used"] == "test-model"
    assert payload["translated_text"]["title"] == "Titulo Traducido"
    assert payload["translated_text"]["body"] == "Cuerpo Traducido"
    assert payload["translated_text"]["section"] == "Seccion Traducida"


@pytest.mark.asyncio
async def test_translate_endpoint_returns_500_when_service_raises(async_client, monkeypatch):
    async def fake_translate(self, request):
        raise RuntimeError("Ollama unreachable")

    monkeypatch.setattr("services.translation_service.TranslationService.translate", fake_translate)

    response = await async_client.post("/api/translate", json=PLAIN_PAYLOAD, headers=AUTH)

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_translate_endpoint_requires_auth_header(async_client):
    response = await async_client.post("/api/translate", json=PLAIN_PAYLOAD)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_translate_endpoint_validates_input_shape(async_client):
    response = await async_client.post("/api/translate", json={"title": "Hello"}, headers=AUTH)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_translate_endpoint_rejects_wrong_method(async_client):
    response = await async_client.get("/api/translate", headers=AUTH)

    assert response.status_code == 405
