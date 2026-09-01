import pytest

import utils.translation.translate_html_content as _thc_mod
from utils.translation.translate_html_content import TranslateHTMLContent


@pytest.mark.asyncio
async def test_html_translation_returns_reconstructed_html(monkeypatch):
    async def fake_translation(prompt, timeout, base_url, model=None, retries=3):
        assert 'Return ONLY the translated "text" values.' in prompt
        return "Hola"

    monkeypatch.setattr(_thc_mod, "generate_translation", fake_translation)

    result = await TranslateHTMLContent().translate_html_content(
        "<p>Hello</p>", "Spanish"
    )

    assert result == "<p>Hola</p>"
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_img_segment_is_not_processed_as_text_before_inline_segment(monkeypatch):
    calls = []

    async def fake_translation(prompt, timeout, base_url, model=None, retries=3):
        calls.append(prompt)
        return "Hola"

    monkeypatch.setattr(_thc_mod, "generate_translation", fake_translation)

    result = await TranslateHTMLContent().translate_html_content(
        '<p>Hello</p><img src="https://example.com/a.jpg" alt="A"><p><strong>World</strong></p>',
        "Spanish",
    )

    assert len(calls) == 2
    assert '<img src="https://example.com/a.jpg" alt="A" />' in result
