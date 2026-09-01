import pytest

from app.utils.translation.translate_html_utils import TranslateHTMLUtils
import app.utils.translation.translate_html_utils as html_utils_mod


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
    # Patch BeautifulSoup inside the module so the method's internal try/except
    # fallback path runs, rather than patching the method itself.
    html = "<div><div><p>The new Slot coordinator</p></div></div>"
    utils = TranslateHTMLUtils()

    def failing_bs(html_content, parser):
        raise Exception("boom")

    monkeypatch.setattr(html_utils_mod, 'BeautifulSoup', failing_bs)

    # extract_text_with_structure should catch the BeautifulSoup failure and
    # fall back to the regex-based old method, returning a 'fallback' structure_map.
    text_segments, structure_map = utils.extract_text_with_structure(html)
    assert isinstance(text_segments, list)
    assert structure_map.get("type") == "fallback"
