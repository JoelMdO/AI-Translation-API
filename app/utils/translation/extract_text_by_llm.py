"""
Extract service for handling communication with the extraction logic
Manages all interactions with the extraction service with HTML preservation
"""
import httpx
from typing import Tuple, Dict, Any
import logging
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ExtractTextByLlm:
    """Service class for extracting text from HTML content by the LLM"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.timeout = 960.0
        self.model = "llama3.2"
        # self.timeout = 60.0
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is accessible
        
        Returns:
            True if Ollama is responding, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def extract_text_with_structure_byLLM(self, html_content: str):
        """
        Extract all translatable text from HTML while preserving complete structure for reconstruction
        Args:
            html_content: HTML string with content to translate
            LLM Json structure.
        Returns:
            LLM returns a JSON with structure and text segments as:
            [
            {
                "type": "paragraph",
                "tag": "h2",
                "content": [
                { "type": "text", "text": "The Digital Overwhelm" }
                ]
            },
            {
                "type": "paragraph",
                "tag": "p",
                "content": [
                { "type": "text", "text": "In our" },
                {
                    "type": "formatted",
                    "tag": "strong",
                    "content": [
                    { "type": "text", "text": "hyperconnected" }
                    ]
                },
                { "type": "text", "text": "world..." }
                ]
            },
            {
                "type": "image",
                "src": "hero.jpg",
                "alt": ""
            },
            { "type": "separator" },
            ]
        """
        try:
            json_structure: Tuple[Dict[str, Any], ...] = (
                            {
                                "type": "paragraph",
                                "tag": "..",
                                "content": [
                                { "type": "text", "text": "..r" },
                                {
                                    "type": "formatted",
                                    "tag": "..",
                                    "content": [
                                    { "type": "text", "text": ".." }
                                    ]
                                },
                                { "type": "text", "text": ".." }
                                ]
                            },
                        )
            logger.info("DEBUG: Starting to get CHUNKS, HTML translation with structure preservation")
            logger.info("DEBUG: Original HTML content: %s", html_content[:500])  # Log first 500 chars for brevity
            # Log first 500 chars for brevity
            print(f"DEBUG: Starting HTML translation at translate html contentwith improved structure preservation")
            prompt = f"""
                        RETURN a JSON with the structure of the HTML content and all translatable text segments.
                        The JSON structured follows {json_structure}.
                        After the fist <div> tag, the content must be structured following the herachy of the HTML tags, 
                        preserving the original HTML structure and tags, if there is no h2, h3, h4, h5, h6, then the content
                        must be wrapped in a <p> tag where each will become a type paragraph on the JSON structure.
                        if any inline tag is found, it must be preserved in the JSON structure as a type formatted with the tag and content.
                        The JSON must be returned as a single string, without any extra text or explanation.
                        The HTML content is: {html_content}
                        """
            print(f"DEBUG: Generated prompt for structured translation")
            timeout_cfg = httpx.Timeout(self.timeout, connect=self.timeout, read=self.timeout)
            request_url = f"{self.base_url}/api/generate"
            try:
                async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                    use_model = self.model
                    payload = { # type: ignore
                        "model": use_model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3,
                        "keep_alive": "-1m",
                    }
                    logger.info("Ollama request: model=%s timeout=%.1f attempt=%d", use_model)
                    response = await client.post(request_url, json=payload)  # type: ignore
                    logger.info("Ollama response status=%s body=%s", response.status_code, (response.text or '')[:1000])
                    response.raise_for_status()
                    return response.json()["response"]
            except httpx.RequestError as e:
                logger.exception(
                    "Ollama request error: url=%s type=%s detail=%r",
                    request_url,
                    type(e).__name__,
                    e,
                )
                raise Exception(
                    f"Ollama request error: {type(e).__name__}: {e!r} "
                    f"(url={request_url})"
                ) from e
        except Exception as e:
            logger.exception("Failed to extract text with structure from HTML")
            raise Exception(
                f"Failed to extract text with structure from HTML: "
                f"{type(e).__name__}: {e!r}"
            ) from e
