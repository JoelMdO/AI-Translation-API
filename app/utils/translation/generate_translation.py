import httpx
from config import OLLAMA_BACKUP_MODEL, OLLAMA_DEFAULT_MODEL

async def generate_translation(prompt: str, timeout: float, base_url: str) -> str:
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
            async with httpx.AsyncClient(timeout=timeout) as client:
                payload: object = {}
                # print(f"DEBUG: PROMPT: {prompt}")
                payload = {
                    "model": OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3  # Lower temperature for consistent translations
                }
                
                response = await client.post(
                    f"{base_url}/api/generate",
                    json=payload
                ) 
                # //TODO change app before deploying
                # response = await client.post("http://localhost:11434/api/generate", json=payload)

                # print(f"DEBUG: Response status code: {response}")
                response.raise_for_status()
                # print(f"DEBUG: Response status code: {response.status_code}")
                # print(f"DEBUG: Response headers: {response.headers}")
                # print(f"DEBUG: Response content: {response.content}...")
                data = response.json()
                return data.get("response", "").strip()
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Translation service error: {str(e)}")