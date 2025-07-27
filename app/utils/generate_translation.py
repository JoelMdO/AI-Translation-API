"""
Ollama service for handling communication with Ollama container
Manages all interactions with the Ollama translation service with HTML preservation
"""
import httpx
import re
from typing import List, Tuple, Match, Optional
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL


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

    def extract_text_from_html(self, html_content: str) -> Tuple[List[str], str]:
        """
        Extract translatable text from HTML while preserving structure
        
        Args:
            html_content: HTML string with content to translate
            
        Returns:
            Tuple of (list of text segments, template with placeholders)
        """
        # Find all text content between HTML tags (but not within tag attributes)
        # This regex captures text that's not inside < >
        text_pattern = r'>([^<]+)<'
        
        # Find all text segments
        text_segments: List[str] = []
        placeholder_template = html_content
        
        # Replace text content with numbered placeholders
        def replace_text(match: Match[str]) -> str:
            text = match.group(1).strip()
            if text:  # Only process non-empty text
                placeholder = f"{{TEXT_{len(text_segments)}__}}"
                text_segments.append(text)
                return f">{placeholder}<"
            return match.group(0)
        
        placeholder_template = re.sub(text_pattern, replace_text, placeholder_template)
        
        # Also handle text at the beginning and end that might not be wrapped in tags
        # Handle text before first tag
        if not placeholder_template.startswith('<'):
            first_tag_match = re.search(r'<', placeholder_template)
            if first_tag_match:
                start_text = placeholder_template[:first_tag_match.start()].strip()
                if start_text:
                    placeholder = f"{{TEXT_{len(text_segments)}__}}"
                    text_segments.append(start_text)
                    placeholder_template = placeholder + placeholder_template[first_tag_match.start():]
        
        # Handle text after last tag
        if not placeholder_template.endswith('>'):
            last_tag_match = None
            for match in re.finditer(r'>', placeholder_template):
                last_tag_match = match
            if last_tag_match:
                end_text = placeholder_template[last_tag_match.end():].strip()
                if end_text:
                    placeholder = f"{{TEXT_{len(text_segments)}__}}"
                    text_segments.append(end_text)
                    placeholder_template = placeholder_template[:last_tag_match.end()] + placeholder
        
        return text_segments, placeholder_template

    def reconstruct_html(self, translated_segments: List[str], template: str) -> str:
        """
        Reconstruct HTML by replacing placeholders with translated text
        
        Args:
            translated_segments: List of translated text segments
            template: HTML template with placeholders
            
        Returns:
            HTML with translated content
        """
        result = template
        for i, translated_text in enumerate(translated_segments):
            placeholder = f"{{TEXT_{i}__}}"
            result = result.replace(placeholder, translated_text)
        
        return result

    async def translate_html_content(self, content: str, target_language: str, model: Optional[str] = None) -> str:
        """
        Translate HTML content while preserving structure and tags
        
        Args:
            content: HTML content to translate
            target_language: Target language for translation
            model: Ollama model to use for translation (defaults to OLLAMA_DEFAULT_MODEL)
            
        Returns:
            Translated HTML content with preserved structure
        """
        # Ensure we have a valid model
        if model is not None:
            model_to_use: str = model
        else:
            model_to_use = OLLAMA_DEFAULT_MODEL or "llama3.2"  # Fallback if env var is not set
        
        # Extract text segments and create template
        text_segments, placeholder_template = self.extract_text_from_html(content)
        
        if not text_segments:
            return content  # No text to translate
        
        # Create prompt for batch translation
        text_to_translate = "---SEGMENT---".join(text_segments)
        prompt = f"""Translate the following text segments to {target_language}. 
Keep the same number of segments separated by ---SEGMENT---. 
Only translate the text content, do not modify the structure or add explanations:

{text_to_translate}"""

        # Get translation
        translated_combined = await self.generate_translation(prompt, model_to_use)
        
        # Split back into segments
        translated_segments = translated_combined.split("---SEGMENT---")
        translated_segments = [seg.strip() for seg in translated_segments]
        
        # Ensure we have the same number of segments
        if len(translated_segments) != len(text_segments):
            # Fallback: translate each segment individually
            translated_segments: List[str] = []
            for segment in text_segments:
                individual_prompt = f"Translate this text to {target_language}: {segment}"
                translated_segment = await self.generate_translation(individual_prompt, model_to_use)
                translated_segments.append(translated_segment.strip())
        
        # Reconstruct HTML with translated text
        return self.reconstruct_html(translated_segments, placeholder_template)

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
