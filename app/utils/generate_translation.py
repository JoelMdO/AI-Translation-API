"""
Ollama service for handling communication with Ollama container
Manages all interactions with the Ollama translation service
"""
import httpx
from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL


class OllamaService:
    """Service class for interacting with Ollama"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 60.0
    
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

    async def generate_translation(self, prompt: str, model: str) -> str:
        """
        Generate translation using Ollama
        
        Args:
            prompt: Translation prompt
            model: Ollama model to use
            
        Returns:
            Generated translation text
            
        Raises:
            Exception: If translation fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload: object = {}
                payload = {
                    "model": OLLAMA_DEFAULT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3  # Lower temperature for consistent translations
                }
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("response", "").strip()
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Translation service error: {str(e)}")


# Global service instance
ollama_service = OllamaService()
