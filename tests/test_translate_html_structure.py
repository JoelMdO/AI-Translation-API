import pytest

from app.utils.translation.translate_html_utils import TranslateHTMLUtils


def test_extract_and_reconstruct_structure_basic():
    html = "<div><div><p>The new Slot coordinator</p></div></div>"
    utils = TranslateHTMLUtils()

    text_segments, structure_map = utils.extract_text_with_structure(html)

    # Verify extraction
    assert isinstance(text_segments, list)
    assert text_segments == ["The new Slot coordinator"]

    # Simulate a translated segment (e.g., Spanish)
    translated_segments = ["El nuevo coordinador de Slot"]

    reconstructed = utils.reconstruct_html_from_structure(translated_segments, structure_map)

    # Expected reconstruction should preserve original tags and substitute translated text
    assert reconstructed == "<div><div><p>El nuevo coordinador de Slot</p></div></div>"


def test_fallback_old_template_used_when_structure_fails(monkeypatch):
    # Force extract_text_with_structure to raise and exercise fallback to old template
    html = "<div><div><p>The new Slot coordinator</p></div></div>"
    utils = TranslateHTMLUtils()

    def fake_extract(html_content):
        raise Exception("boom")

    monkeypatch.setattr(utils, "extract_text_with_structure", fake_extract)

    # Now call and ensure fallback still returns text segments and a structure_map of fallback type
    text_segments, structure_map = utils.extract_text_with_structure(html)
    assert isinstance(text_segments, list)
    assert structure_map.get("type") == "fallback"
