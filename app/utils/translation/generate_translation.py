import asyncio
import httpx
from config import OLLAMA_BACKUP_MODEL, OLLAMA_DEFAULT_MODEL
import logging

logger = logging.getLogger(__name__)


async def generate_translation(prompt: str, timeout: float, base_url: str, model: str | None = None, retries: int = 3) -> str:
    attempt = 0
    cur_timeout = timeout
    while True:
        try:
            timeout_cfg = httpx.Timeout(cur_timeout)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                use_model = model or OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL
                payload = { # type: ignore
                    "model": use_model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                }

                logger.info("Ollama request: model=%s timeout=%.1f attempt=%d", use_model, cur_timeout, attempt+1)
                response = await client.post(f"{base_url}/api/generate", json=payload)  # type: ignore
                logger.info("Ollama response status=%s body=%s", response.status_code, (response.text or '')[:1000])
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
                except ValueError:
                    raise Exception(f"Ollama returned non-JSON response: {response.text}")

                if isinstance(data, dict):
                    if "response" in data and isinstance(data["response"], str):
                        logging.info("Type DATA RESPONSE from Ollama")
                        return data["response"].strip()

                    if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                        first = data["choices"][0] #type: ignore
                        if isinstance(first, dict) and "text" in first and isinstance(first["text"], str):
                            logging.info("Type DATA CHOICES from Ollama")
                            return first["text"].strip()

                    if "data" in data and isinstance(data["data"], list):
                        for item in data["data"]: #type: ignore
                            if isinstance(item, dict) and "content" in item:
                                for c in item["content"]: #type: ignore
                                    if isinstance(c, dict) and c.get("type") == "output_text" and "text" in c: #type: ignore
                                        logging.info("Type DATA CONTENT from Ollama")
                                        return c["text"].strip() #type: ignore

                    for key in ("text", "result"):
                        if key in data and isinstance(data[key], str):
                            logging.info("Type DATA KEY from Ollama: %s", key)
                            return data[key].strip() #type: ignore

                def _find_text(obj): # type: ignore
                    if isinstance(obj, str):
                        return obj
                    if isinstance(obj, dict):
                        for v in obj.values(): # type: ignore
                            t = _find_text(v) # type: ignore
                            if t:
                                return t # type: ignore
                    if isinstance(obj, list):
                        for v in obj:# type: ignore
                            t = _find_text(v) # type: ignore
                            if t:
                                return t # type: ignore
                    return None

                found = _find_text(data) # type: ignore
                if found:
                    return found.strip() # type: ignore

                raise Exception(f"Unexpected Ollama response format: {data}")

        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            attempt += 1
            logger.warning("Timeout from Ollama (attempt %d/%d): %s", attempt, retries + 1, str(e))
            if attempt > retries:
                raise Exception(f"Translation service timeout after {attempt} attempts: {str(e)}")
            backoff = 0.5 * (2 ** (attempt - 1))
            cur_timeout = min(cur_timeout * 1.5, 300)
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