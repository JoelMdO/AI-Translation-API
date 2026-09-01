"""
Translate HTML content while preserving structure using Yag and Ollama LLM
Manages all interactions with the Ollama translation service with HTML preservation
"""
from typing import List
from utils.translation.generate_translation import generate_translation
from utils.translation.create_prompt_translation import create_prompt_translation
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL, OLLAMA_REQUEST_TIMEOUT
import logging
from utils.translation.extract_text import ExtractText
from utils.translation.regenerate_article import RegenerateArticle
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslateHTMLContent:
    """Service class for interacting with Ollama"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = OLLAMA_REQUEST_TIMEOUT
        self.model = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL 
    
    async def translate_html_content(self, content: str, target_language: str) -> str:
        """
        Translate HTML content while preserving structure and tags
        Uses improved text extraction that sends only plain text to Llama3.2 or backup model Ollama.
        
        Args:
            content: HTML content to translate
            target_language: Target language for translation
            
        Returns:
            Translated HTML content with preserved structure
        """
        if not content:
            raise RuntimeError(f"No content received: {content}")
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured.")

        try:
            text_segments: List[dict[str, str]] = await ExtractText().extract_article_structure(content)
            print(f"DEBUG EXTRACTED JSON: Extracted text segments for translation: {text_segments}")
            translated_segments: List[dict[str, str]] = []
            for text in text_segments:
                tag = text.get("tag")
                if tag in {"hr", "figure", "img", "figcaption"} or "text" not in text:
                    print(f"DEBUG: For STRUCTURAL TAG: Preserving HTML segment {text})")
                    translated_segments.append(text)
                    continue
                else:             
                    print(f"DEBUG: For TEXT IN TEXT_SEGMENTS: Translating HTML segment {text['text']}... (id: {text['id']})")
                    prompt = await create_prompt_translation(
                        text=text["text"],  # type: ignore
                        type="html",
                        target_language=target_language,
                    )
                    print(f"DEBUG: Generated prompt for segment {text['id']}: {prompt[:100]}...")  # Log first 100 chars of prompt
                    translation = await generate_translation(
                        prompt,
                        timeout=self.timeout,
                        base_url=self.base_url,
                        model=self.model,
                        retries=3,
                    )
                    if not translation:
                        raise RuntimeError(f"Empty translation for HTML segment {text['id']}") # type: ignore
 
                    if text["tag"] in {"strong", "b", "em", "i", "u", "s"}:
                        index_to_insert = len(translated_segments) - 1
                        print(f"DEBUG: For INLINE TAG: Inserting translated segment at index {index_to_insert} for tag {text['tag']} with id {text['id']}.")
                        if (
                            index_to_insert >= 0
                            and index_to_insert < len(translated_segments)
                            and "text" in translated_segments[index_to_insert]
                        ):
                            new_segment = f"<{text['tag']}>{translation}</{text['tag']}>"
                            print(f"DEBUG: New segment to insert: {new_segment}")
                            print(f"DEBUG: Current translated_segments before insertion: {translated_segments}")
                            # Insert the new segment into the existing segment at the correct index
                            print(f"DEBUG: Index to insert: {index_to_insert}") 
                            prev_segment = translated_segments[index_to_insert]["text"]
                            if prev_segment.startswith('"') and prev_segment.endswith('"') or prev_segment.startswith("'") and prev_segment.endswith("'"):
                                prev_segment = prev_segment[1:-1]  # Remove the surrounding quotes
                            print(f"DEBUG: Previous segment before insertion: {prev_segment}")
                            # Concatenate the previous segment with the new segment
                            print(f"DEBUG: Previous segment at index {index_to_insert}: {prev_segment}")
                            translated_segments[index_to_insert]["text"] = prev_segment + new_segment
                            print(f"DEBUG: Updated segment at index {index_to_insert}: {translated_segments[index_to_insert]}")
                        else:
                            logger.warning(f"Could not find index to insert for tag {text['tag']} with id {text['id']}. Appending instead.")
                            translated_segments.append({"id": text["id"], "tag": text["tag"], "text": translation})
                    else:    
                        translated_segments.append({"id": text["id"], "tag": text["tag"], "text": translation})
            print(f"DEBUG FINALLY: Translated segments: {translated_segments}")
            text_translated_segments = RegenerateArticle().reconstruct_html_from_structure(translated_segments)
            return text_translated_segments
        except Exception:
            logger.exception("HTML translation failed; returning original HTML")
            raise RuntimeError(f"HTML translation failed for content: {content}")


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
        if not text:
            return text
        if self.base_url is None:
            raise RuntimeError("OLLAMA_BASE_URL is not configured.")
        assert isinstance(self.base_url, str)
        if self.model is None:
            raise RuntimeError("OLLAMA_MODEL is not configured.")
        assert isinstance(self.model, str)

        try:
            prompt = await create_prompt_translation(
                                text=text,  # type: ignore
                                type="html",
                                target_language=target_language,
                            )
            translation = await generate_translation(
                                prompt,
                                timeout=self.timeout,
                                base_url=self.base_url,
                                model=self.model,
                                retries=3,
                            )
            if not translation:
                logger.warning("translate_plain_text: empty response, returning original")
                return text
            return translation
        except Exception:
            logger.exception("translate_plain_text failed, returning original text")
            return text

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
