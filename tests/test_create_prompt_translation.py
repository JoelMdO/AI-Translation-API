import pytest

from app.utils.translation import create_prompt_translation as cpt_mod

@pytest.mark.asyncio
async def test_create_prompt_translation_includes_language_and_rules(monkeypatch): #type: ignore
    # Monkeypatch get_style_rules and build_context_block imported names inside the module
    monkeypatch.setattr(cpt_mod, 'get_style_rules', lambda lang: ['Use formal tone', 'Avoid slang']) #type: ignore
    async def fake_build_context(text, lang): #type: ignore
        return 'RAG-CONTEXT'

    monkeypatch.setattr(cpt_mod, 'build_context_block', fake_build_context) #type: ignore

    prompt = await cpt_mod.create_prompt_translation(type='raw', text='Hello world', target_language='Spanish', title='T', body='B', section='S')
    assert 'Spanish' in prompt
    assert 'Use formal tone' in prompt
    assert 'RAG-CONTEXT' in prompt or 'No RAG context' in prompt
    assert 'Return the translation in this exact format' in prompt
