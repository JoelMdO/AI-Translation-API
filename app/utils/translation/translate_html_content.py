"""
Translate HTML content while preserving structure using Yag and Ollama LLM
Manages all interactions with the Ollama translation service with HTML preservation
"""
from typing import List
from utils.translation.generate_translation import generate_translation
from utils.translation.translate_html_utils import TranslateHTMLUtils
from utils.translation.create_prompt_translation import create_prompt_translation
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
##//TODO remove app before deploying 
# from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class TranslateHTMLContent:
    """Service class for interacting with Ollama"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 60.0
        self.model = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL  # Fallback if env var is not set
    
    async def translate_html_content(self, content: str, target_language: str) -> str: 
        """
        Translate HTML content while preserving structure and tags
        Uses improved text extraction that sends only plain text to Aya or backup model Ollama.
        
        Args:
            content: HTML content to translate
            target_language: Target language for translation
            
        Returns:
            Translated HTML content with preserved structure
        """
        # Try new structured approach first
        if not content or len(content.strip()) < 5:
            return content
        # Ensure base_url is configured and non-None for type-safety
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured. Set OLLAMA_BASE_URL in config.")
        assert isinstance(self.base_url, str)
        # Ensure model is configured and non-None for type-safety
        if self.model is None:
            raise RuntimeError("OLLAMA_MODEL is not configured. Set OLLAMA_MODEL in config.")
        assert isinstance(self.model, str)
    
        try:
            print(f"DEBUG: Starting HTML translation with structure preservation")
            chunks = TranslateHTMLUtils().split_html_into_chunks(content, max_chars=5000)
            translated_chunks: List[str] = []
            for i, chunk in enumerate(chunks):
                try:
                    # Extract plain text segments and a placeholder template that preserves the HTML structure
                    text_segments, placeholder_template = TranslateHTMLUtils().extract_text_from_html(chunk)

                    if not text_segments:
                        translated_chunks.append(chunk)
                        continue

                    # Send only plain text (no HTML tags) to the LLM
                    text_to_translate = "---SEGMENT---".join(text_segments)
                    instructions = await create_prompt_translation(type="html", text=text_to_translate, target_language=target_language)
                    prompt = f"""{instructions}\n
                    The text to translate is:
                    {text_to_translate}"""

                    print(f"DEBUG: Generated prompt for translation of chunk {i+1}")

                    translated_response = await generate_translation(prompt, timeout=self.timeout, base_url=self.base_url)
                    print("==="*40)
                    print(f"DEBUG: Raw translation response: {translated_response}")
                    print("==="*40)

                    if not translated_response or len(translated_response.strip()) < 5:
                        print(f"WARNING: Empty or invalid translation for chunk {i+1}")
                        translated_chunks.append(chunk)
                        continue

                    # Split response back into segments and reconstruct HTML
                    translated_segments = [seg.strip() for seg in translated_response.split("---SEGMENT---")]

                    if len(translated_segments) != len(text_segments):
                        # Fallback: translate each segment individually to ensure counts match
                        translated_segments = []
                        for segment in text_segments:
                            individual_prompt = f"Translate this text to {target_language}: {segment}"
                            translated_segment = await generate_translation(individual_prompt, timeout=self.timeout, base_url=self.base_url)
                            translated_segments.append(translated_segment.strip())

                    reconstructed = TranslateHTMLUtils().reconstruct_html(translated_segments, placeholder_template)
                    translated_chunks.append(reconstructed)

                except Exception as chunk_error:
                    print(f"ERROR: Failed to translate chunk {i+1}: {str(chunk_error)}")
                    translated_chunks.append(chunk)
                    continue

            result = "\n".join(translated_chunks)
            print("==="*40)
            print(f"DEBUG: Final translated HTML result: {result}")
            print("==="*40)
            return result

        except Exception as e:
            print(f"DEBUG: Error in structured translation: {e}. Falling back to old method.")
            return await self._translate_html_content_old_method(content, target_language)


    # OLD METHOD - PRESERVED FOR FALLBACK
    async def _translate_html_content_old_method(self, content: str, target_language: str) -> str:
        """
        OLD METHOD: Translate HTML content while preserving structure and tags
        This method uses the original segment-based approach with ---SEGMENT--- separators
        """
        # Extract text segments and create template
        text_segments, placeholder_template = TranslateHTMLUtils().extract_text_from_html(content)
        
        if not text_segments:
            return content  # No text to translate
        
        # Ensure base_url is configured and non-None for type-safety
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured. Set OLLAMA_BASE_URL in config.")
        assert isinstance(self.base_url, str)

        # Create prompt for batch translation
        text_to_translate = "---SEGMENT---".join(text_segments)
        print(f"DEBUG: OLD METHOD - text for translation: {text_to_translate}")
        
        # OLD PROMPT - PRESERVED FOR REFERENCE
        # Create prompt for translation with numbered segments
        instructions = await create_prompt_translation(type="html", text=text_to_translate, target_language=target_language)
        prompt = f"""{instructions}\n
        The text to translate is:
        {text_to_translate}"""
        # print(f"DEBUG: Generated prompt for translation: {prompt}")
        translated_combined = await generate_translation(prompt, timeout=self.timeout, base_url=self.base_url)
        
        # OLD DEBUG - PRESERVED FOR REFERENCE
        # print(f"DEBUG: Raw translation response: {translated_combined}")
        
        # Split back into segments
        translated_segments = translated_combined.split("---SEGMENT---")
        translated_segments = [seg.strip() for seg in translated_segments]
        
        # Ensure we have the same number of segments
        if len(translated_segments) != len(text_segments):
            # Fallback: translate each segment individually
            translated_segments: List[str] = []
            for segment in text_segments:
                individual_prompt = f"Translate this text to {target_language}: {segment}"
                translated_segment = await generate_translation(individual_prompt, timeout=self.timeout, base_url=self.base_url)
                translated_segments.append(translated_segment.strip())
        
        # Reconstruct HTML with translated text
        print(f"DEBUG: OLD METHOD - HTML with translated content: {TranslateHTMLUtils().reconstruct_html(translated_segments, placeholder_template)}")
        return TranslateHTMLUtils().reconstruct_html(translated_segments, placeholder_template)

    async def translate_raw_content(self, text: str, title: str, body: str, section: str, target_language: str) -> str:
        """
        Simple translation of raw text without HTML structure preservation
        """
        # Ensure base_url is configured and non-None for type-safety
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured. Set OLLAMA_BASE_URL in config.")
        assert isinstance(self.base_url, str)

        prompt = await create_prompt_translation(type="raw", text=text, target_language=target_language, title=title, body=body, section=section)

        raw_translation = await generate_translation(
            prompt=prompt, timeout=self.timeout, base_url=self.base_url)
        return raw_translation
# Global service instance
translateHTMLContent = TranslateHTMLContent()
