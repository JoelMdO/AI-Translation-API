import pytest

from schemas.translation import TranslationRequest
from services import translation_service


@pytest.mark.asyncio
async def test_service_accepts_structural_segments_without_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image and separator segments must not turn a valid translation into a 500."""

    async def fake_html_translation(
        content: str,
        target_language: str,
    ) -> list[dict[str, object]]:
        return [
            {"id": 1, "tag": "p", "text": "Hola"},
            {
                "id": 2,
                "tag": "img",
                "src": "https://example.com/image.jpg",
                "alt": "Example",
            },
            {"id": 3, "tag": "hr"},
        ]

    async def fake_plain_translation(text: str, target_language: str) -> str:
        return f"translated: {text}"

    monkeypatch.setattr(
        translation_service.translateHTMLContent,
        "translate_html_content",
        fake_html_translation,
    )
    monkeypatch.setattr(
        translation_service.translateHTMLContent,
        "translate_plain_text",
        fake_plain_translation,
    )

    response = await translation_service.TranslationService().translate(
        TranslationRequest(
            title="Title",
            body='<p>Hello</p><img src="https://example.com/image.jpg"><hr>',
            section="News",
            target_language="Spanish",
        )
    )

    assert response.status == 200
    dumped_body = response.model_dump()["translated_text"]["body"]
    assert dumped_body[1]["src"] == "https://example.com/image.jpg"
    assert dumped_body[2]["text"] is None
