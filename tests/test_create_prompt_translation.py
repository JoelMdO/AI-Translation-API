import pytest

from app.utils.translation import create_prompt_translation as cpt_mod

@pytest.mark.asyncio
async def test_create_prompt_translation_includes_language_and_rules(): #type: ignore
    prompt = await cpt_mod.create_prompt_translation(type='raw', text='Hello world', target_language='Spanish', title='T', body='B', section='S')
    assert 'Spanish' in prompt
    assert 'Hello world' in prompt
    assert 'Return ONLY the translated' in prompt
