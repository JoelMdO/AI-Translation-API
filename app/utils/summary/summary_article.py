"""
Summary service for handling communication with Ollama container
Manages all interactions with the Ollama summary creation service with HTML preservation
"""
import httpx
from utils.translation.generate_translation import generate_translation
from utils.summary.create_prompt_summary import create_prompt_summary
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
##//TODO remove app before deploying 
# from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class SummaryUtils:
    """Service class for summarizing HTML content while preserving structure using Ollama LLM"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 90.0
        self.model = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL  # Fallback if env var is not set
    
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

    async def resume_article(self, title: str, body: str, model: str, language: str, context_block: str = "") -> str:
        """
        Generate a resume for the given article text.
        context_block: optional RAG style-reference prefix prepended to the prompt.
        """
        resume = ""
        # Ensure base_url is configured and non-None for type-safety
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured. Set OLLAMA_BASE_URL in config.")
        assert isinstance(self.base_url, str)

        try:
            print(f"DEBUG: Original article text: {title}")
            prompt = await create_prompt_summary(type="raw", text=body, target_language=language, title=title, body=body, section=None)
            resume = await generate_translation(prompt=prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
            print(f"DEBUG: Generated resume english: {resume}")
            print(f"DEBUG: Generated resume spanish: {resume}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception("Summary generation failed.") from e
        return resume

# Global service instance
summary_utils = SummaryUtils()
