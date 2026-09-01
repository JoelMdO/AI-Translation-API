import json
from pathlib import Path

import pytest

from app.utils.translation.extract_text_by_llm import ExtractTextByLlm


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_with_structure_from_html(capsys):

    ## TO RUN
    ## cd AI-Translation-API
    ## PYTHONPATH=.:app pytest --noconftest -q tests/test_extract_text_by_llm.py

    ARTICLE_SLOTS = json.loads(
    (Path(__file__).parent / "data" / "article_slots.json").read_text()
)["article_1"]["text"]

    result = await ExtractTextByLlm().extract_text_with_structure_byLLM(
        html_content=ARTICLE_SLOTS,
    )

    # Pytest captures stdout by default. Disable capture for this diagnostic output.
    with capsys.disabled():
        print("Extracted text with structure:", result, flush=True)

    assert isinstance(result, str)
