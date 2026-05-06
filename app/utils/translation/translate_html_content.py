"""
Translate HTML content while preserving structure using Yag and Ollama LLM
Manages all interactions with the Ollama translation service with HTML preservation
"""
from typing import List
from utils.translation.generate_translation import generate_translation
from utils.translation.translate_html_utils import TranslateHTMLUtils
from utils.translation.create_prompt_translation import create_prompt_translation
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
import logging

logger = logging.getLogger(__name__)
##//TODO remove app before deploying 
# from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class TranslateHTMLContent:
    """Service class for interacting with Ollama"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 120.0
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
        logger.info(f"DEBUG: Starting HTML translation with content: {content[:100]}... (type: {type(content)})")
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
            logger.info(f"DEBUG: Starting to get CHUNKS, HTML translation with structure preservation")
            chunks: List[str] = TranslateHTMLUtils().split_html_into_chunks(content, max_tokens=300)
            translated_chunks: List[str] = []
            for i, chunk in enumerate(chunks):
                logger.info("====================")
                logger.info("Chunk %d: Processing chunk of length %d", i+1, len(chunk))
                logger.info("Chunk %d: %s", i+1, chunk)
                logger.info("====================")
                try:
                    # Extract plain text segments and a structure map that preserves the HTML structure
                    text_segments, structure_map = TranslateHTMLUtils().extract_text_with_structure(chunk)
                    logger.info("Extracted text segments for translation %s", text_segments)
                    logger.info("Extracted structure map for translation %s", structure_map)
                    if not text_segments:
                        translated_chunks.append(chunk)
                        continue

                    # Send only plain text (no HTML tags) to the LLM
                    text_to_translate = "---SEGMENT---".join(text_segments)
                    logger.info("Chunk %d: Prepared text for translation (length: %d)", i+1, len(text_to_translate))
                    prompt = await create_prompt_translation(type="html", text=text_to_translate, target_language=target_language)
                   

                    logger.info("====================")
                    logger.info("Chunk %d: Generated prompt for translation: %s", i+1, prompt)
                    logger.info("====================")

                    translated_response = await generate_translation(prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
                    logger.info("Chunk %d: Raw translation response: %s", i+1, translated_response)

                    if not translated_response or len(translated_response.strip()) < 5:
                        logger.warning("Chunk %d: Empty or invalid translation", i+1)
                        translated_chunks.append(chunk)
                        continue

                    # =================================
                    # Split response back into segments and reconstruct HTML
                    # =================================
                    translated_segments = [seg.strip() for seg in translated_response.split("---SEGMENT---")]
                    logger.info("Chunk %d: Translated into %d segments", i+1, len(translated_segments))
                    if len(translated_segments) != len(text_segments):
                        # Fallback: If LLM does not preserve structure, will translate each segment individually to ensure counts match.
                        # Each call is wrapped so a single failure uses the original segment
                        # rather than aborting the entire chunk.
                        logger.warning(
                            "Chunk %d: Segment count mismatch (got %d, expected %d). "
                            "Falling back to per-segment translation.",
                            i+1, len(translated_segments), len(text_segments)
                        )
                        translated_segments = []
                        for seg_idx, segment in enumerate(text_segments):
                            try:
                                individual_prompt = f"Translate this text to {target_language}: {segment}"
                                translated_segment = await generate_translation(
                                    individual_prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3
                                )
                                translated_segments.append(translated_segment.strip()) #type: ignore
                            except Exception as seg_error:
                                logger.warning(
                                    "Chunk %d, segment %d: translation failed (%s), keeping original.",
                                    i+1, seg_idx+1, str(seg_error)
                                )
                                translated_segments.append(segment) #type: ignore

                    # Reconstruct using the structured mapper which handles fallback templates
                    reconstructed = TranslateHTMLUtils().reconstruct_html_from_structure(translated_segments, structure_map)
                    translated_chunks.append(reconstructed)

                except Exception as chunk_error:
                    logger.error("Chunk %d: Failed to translate chunk: %s", i+1, str(chunk_error))
                    translated_chunks.append(chunk)
                    continue

            result = "\n".join(translated_chunks)
            logger.info("==================")
            logger.info("Final translated HTML result: %s", result)
            logger.info("==================")
            return result

        except Exception as e:
            logger.error("Error in structured translation: %s. Falling back to old method.", str(e))
            return await self._translate_html_content_old_method(content, target_language)


    async def translate_plain_text(self, text: str, target_language: str) -> str:
        """
        Translate a plain-text string (no HTML tags) using the LLM.
        Used when a field has no HTML markup but another field in the same request does.

        Args:
            text: Plain text to translate
            target_language: Target language for translation

        Returns:
            Translated plain text string
        """
        if not text or len(text.strip()) < 2:
            return text
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured.")
        assert isinstance(self.base_url, str)
        if self.model is None:
            raise RuntimeError("OLLAMA_MODEL is not configured.")
        assert isinstance(self.model, str)

        try:
            instructions = await create_prompt_translation(type="html", text=text, target_language=target_language)
            prompt = f"""{instructions}\nThe text to translate is:\n{text}"""
            translated = await generate_translation(prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
            if not translated or len(translated.strip()) < 2:
                logger.warning("translate_plain_text: empty response, returning original")
                return text
            return translated.strip()
        except Exception:
            logger.exception("translate_plain_text failed, returning original text")
            return text

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
        logger.info("OLD METHOD - text for translation: %s", text_to_translate)
        
        # OLD PROMPT - PRESERVED FOR REFERENCE
        # Create prompt for translation with numbered segments
        instructions = await create_prompt_translation(type="html", text=text_to_translate, target_language=target_language)
        prompt = f"""{instructions}\n
        The text to translate is:
        {text_to_translate}"""
        # logger.info("Generated prompt for translation: %s", prompt)
        translated_combined = await generate_translation(prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
        
        # OLD DEBUG - PRESERVED FOR REFERENCE
        # logger.info("Raw translation response: %s", translated_combined)
        
        # Split back into segments
        translated_segments = translated_combined.split("---SEGMENT---")
        translated_segments = [seg.strip() for seg in translated_segments]
        
        # Ensure we have the same number of segments
        if len(translated_segments) != len(text_segments):
            # Fallback: translate each segment individually
            translated_segments: List[str] = []
            for segment in text_segments:
                individual_prompt = f"Translate this text to {target_language}: {segment}"
                translated_segment = await generate_translation(individual_prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
                translated_segments.append(translated_segment.strip())
        
        # Reconstruct HTML with translated text
        logger.info("OLD METHOD - HTML with translated content: %s", TranslateHTMLUtils().reconstruct_html(translated_segments, placeholder_template))
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
            prompt=prompt, timeout=self.timeout, base_url=self.base_url, model=self.model, retries=3)
        return raw_translation
# Global service instance
translateHTMLContent = TranslateHTMLContent()
