import httpx
import pytest

from app.utils.translation.generate_translation import generate_translation


@pytest.mark.asyncio
async def test_generate_translation_keeps_model_loaded(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = '{"response":"ready"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "ready"}

    async def fake_post(self, url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await generate_translation(
        prompt="ready",
        timeout=1,
        base_url="http://ollama:11434",
        model="aya",
        retries=0,
    )

    assert result == "ready"
    assert captured["json"]["keep_alive"] == "-1m"
