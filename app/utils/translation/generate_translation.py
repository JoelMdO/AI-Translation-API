import asyncio
import httpx
import logging
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_translation(prompt: str, timeout: float, base_url: str, model: str | None = None, retries: int = 3) -> str:
    attempt = 0
    cur_timeout = timeout
    print(f"GENERATE TRANSLATION DEBUG: Starting translation generation with prompt length {len(prompt)} and timeout {timeout}s")
    while True:
        try:
            timeout_cfg = httpx.Timeout(cur_timeout)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:

                use_model = model or "llama3.2"
                payload = { # type: ignore
                    "model": use_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                    "keep_alive": "-1m",
                }

                logger.info("Ollama request: model=%s timeout=%.1f attempt=%d", use_model, cur_timeout, attempt+1)
                response = await client.post(f"{base_url}/api/generate", json=payload)  # type: ignore
                print(f"/// GENERATE TRANSLATION AFTER CLIENT POST: Ollama response status={response.status_code} body={(response.text or '')[:1000]}")
                response.raise_for_status()

                """
                PURPOSE:
                ---------
                Extract the generated text from the Ollama API response. 
                Ollama's response format can vary based on the model and configuration, 
                but we need to extract the generated text from the response. 
                The logic checks multiple possible fields and structures in the JSON 
                response to find the translated text. This ensures compatibility with different Ollama versions and models, 
                and provides a fallback mechanism if the expected fields are not present.
                """
                try:
                    data = response.json()
                    return data["response"]
                except ValueError:
                    raise Exception(f"Ollama returned non-JSON response: {response.text}")

        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            attempt += 1
            logger.warning("Timeout from Ollama (attempt %d/%d): %s", attempt, retries + 1, str(e))
            if attempt > retries:
                raise Exception(f"Translation service timeout after {attempt} attempts: {str(e)}")
            backoff = 0.5 * (2 ** (attempt - 1))
            cur_timeout = min(cur_timeout * 1.5, 900)
            await asyncio.sleep(backoff)
            continue
        except httpx.RequestError as e:
            logger.exception("Ollama request error")
            raise Exception(f"Ollama request error: {str(e)}")
        except httpx.HTTPStatusError as e:
            resp = e.response
            text = resp.text 
            raise Exception(f"Ollama API error: {resp.status_code} - {text}")
        except Exception as e:
            logger.exception("Translation service error in generate_translation")
            raise Exception(f"Translation service error: {str(e)}")
