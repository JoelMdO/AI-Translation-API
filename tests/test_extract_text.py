import pytest
import json
from pathlib import Path
from app.utils.translation.extract_text import ExtractText
from app.utils.translation.create_prompt_translation import create_prompt_translation
from app.utils.translation.generate_translation import generate_translation


@pytest.mark.asyncio
async def test_extract_article_structure_does_not_duplicate_nested_blocks():
    html = "<div><p>One paragraph.</p></div>"

    result = await ExtractText().extract_article_structure(html)

    assert result == [{"id": 1, "tag": "p", "text": "One paragraph."}]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_text_with_structure_from_html(capsys): #type: ignore

    ## TO RUN
    ## cd AI-Translation-API
    ## PYTHONPATH=.:app pytest --noconftest -q tests/test_extract_text_by_llm.py

    ## To see logs
    ## PYTHONPATH=.:app pytest --noconftest -s -q tests/test_extract_text.py

    base_url = "http://localhost:11434"

    ARTICLE_SLOTS = json.loads(
    (Path(__file__).parent / "data" / "article_slots.json").read_text()
)["article_1Small"]["text"]

    result = await ExtractText().extract_article_structure(
        html=ARTICLE_SLOTS,
    )

    newBlocks = []
    # Pytest captures stdout by default. Disable capture for this diagnostic output.
    with capsys.disabled():
            print("Extracted text with structure:", result, flush=True)

    for block in result:
            print("Processing block after EXTRACT with length:", len(block["text"]), flush=True)
            # if len(block["text"]) == 1:  # Change 'results' to 'result' to match the variable name
            prompt = await create_prompt_translation(block["text"], target_language="Spanish")
            translation = await generate_translation(prompt, timeout=10, base_url=base_url)
            block["text"] = translation
            # else:
            #     for sub_block in block["text"]:
            #         prompt = await create_prompt_translation(sub_block["text"], target_language="Spanish")
            #         translation = await generate_translation(prompt, target_language="Spanish", base_url=base_url)
            #         block["text"][block["text"].index(sub_block)] = translation

            newBlocks.extend([block])

    result = newBlocks
    with capsys.disabled():
        print("~~~~~~TRANSLATION:", block, flush=True)

    # backToTranslated = regenerate_json(ARTICLE_SLOTS, result)
    # with capsys.disabled():
    #             print("Back to translated structure:", backToTranslated, flush=True)
    
    assert isinstance(result, list)
    
