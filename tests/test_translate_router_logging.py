import pytest

from routers import translate_router
from schemas.testUser import GoogleUser
from schemas.translation import (
    TranslatedSegment,
    TranslatedText,
    TranslationRequest,
    TranslationResponse,
)


@pytest.mark.asyncio
async def test_translation_response_log_uses_serialized_data(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Debug output should show response data, not Pydantic class reprs."""

    response = TranslationResponse(
        translated_text=TranslatedText(
            title=[TranslatedSegment(id=1, tag="p", text="Nuevo coordinador")],
            body=[TranslatedSegment(id=1, tag="p", text="Contenido")],
            section="Noticias",
        ),
        status=200,
        model_used="test-model",
    )

    class FakeTranslationService:
        async def translate(self, request: TranslationRequest) -> TranslationResponse:
            return response

    monkeypatch.setattr(
        translate_router.translation_service,
        "TranslationService",
        FakeTranslationService,
    )

    result = await translate_router.translate_text(
        request=TranslationRequest(
            title="New slot coordinator",
            body="Content",
            section="News",
        ),
        current_user=GoogleUser(
            user_id="1",
            email="test@example.com",
            name="Test User",
            verified=True,
        ),
    )

    output = capsys.readouterr().out
    assert result == response
    assert "Translation response:" in output
    assert "Nuevo coordinador" in output
    assert "TranslatedText(" not in output
    assert "TranslatedSegment(" not in output


@pytest.mark.asyncio
async def test_translation_endpoint_omits_empty_segment_fields(
    async_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each segment should contain only attributes that have actual values."""

    response = TranslationResponse(
        translated_text=TranslatedText(
            title=[
                {
                    "id": 1,
                    "tag": "p",
                    "text": "Nuevo coordinador",
                    "src": "",
                    "alt": "",
                    "href": "",
                }
            ],
            body=[
                {
                    "id": 2,
                    "tag": "img",
                    "text": None,
                    "src": "https://example.com/image.jpg",
                    "alt": "",
                    "href": None,
                }
            ],
            section="Noticias",
        ),
        status=200,
        model_used="test-model",
    )

    class FakeTranslationService:
        async def translate(self, request: TranslationRequest) -> TranslationResponse:
            return response

    monkeypatch.setattr(
        translate_router.translation_service,
        "TranslationService",
        FakeTranslationService,
    )

    http_response = await async_client.post(
        "/api/translate",
        json={
            "title": "New slot coordinator",
            "body": '<img src="https://example.com/image.jpg">',
            "section": "News",
            "target_language": "Spanish",
        },
        headers={"Authorization": "Bearer devtoken"},
    )

    assert http_response.status_code == 200
    translated = http_response.json()["translated_text"]
    assert translated["title"] == [
        {"id": 1, "tag": "p", "text": "Nuevo coordinador"}
    ]
    assert translated["body"] == [
        {"id": 2, "tag": "img", "src": "https://example.com/image.jpg"}
    ]
