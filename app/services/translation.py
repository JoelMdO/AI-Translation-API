"""
Translation service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
from config import OLLAMA_BACKUP_MODEL, OLLAMA_DEFAULT_MODEL
from utils.sanitize_html import sanitize_html
from utils.sanitize_text import sanitize_text
from utils.translation.translate_html_content import translateHTMLContent
from schemas.translation import TranslationRequest, TranslationResponse
import re
from config import OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
##//TODO remove app before deploying 
# from app.utils.sanitize_html import sanitize_html
# from app.utils.ollama_services import ollama_service
# from app.utils.sanitize_text import sanitize_text
# from app.utils.create_prompt_translation import create_prompt_translation
# from app.schemas.translation import TranslationRequest, TranslationResponse


class TranslationService:
    """Service class for handling translation business logic"""

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Process translation request with HTML content preservation
        Returns an object with translated fields, avoids multiple Ollama calls if possible.
        """
        # Determine the model that will actually be used: env vars take precedence,
        # falling back to the model field in the request so the value is consistent
        # across both success and failure response paths.
        model_used: str = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL or request.model
        try:
            has_html = any('<' in text and '>' in text for text in [request.title, request.body, request.section])
            if has_html:
                # If HTML, translate each field separately (Ollama likely needs to preserve tags)
                translated_title = await translateHTMLContent.translate_html_content(
                    content=request.title, target_language=request.target_language
                )
                translated_body = await translateHTMLContent.translate_html_content(
                    content=request.body, target_language=request.target_language
                )
                translated_section = await translateHTMLContent.translate_html_content(
                    content=request.section, target_language=request.target_language
                )
                # Sanitize only for malicious content, not for structure
                translated_title = sanitize_html(translated_title)
                translated_body = sanitize_html(translated_body)
                translated_section = sanitize_html(translated_section)
            else:
                # For plain text, sanitize and combine into a single prompt for one Ollama call
                sanitized_title = sanitize_text(request.title)
                sanitized_body = sanitize_text(request.body)
                sanitized_section = sanitize_text(request.section)
                sanitized_target_language = sanitize_text(request.target_language)
                # Get translation from Ollama (single call)
                # raw_translation = await ollama_service.generate_translation(
                #     prompt=prompt,
                # )
                raw_translation = await translateHTMLContent.translate_raw_content(
                    text=f"{sanitized_title}\n{sanitized_body}\n{sanitized_section}",
                    title=sanitized_title,
                    body=sanitized_body,
                    section=sanitized_section,
                    target_language=sanitized_target_language,
                )
                print(f"DEBUG: Raw translation response: {raw_translation}")
                # Try to parse the response into fields (assuming format: Título: ... Cuerpo: ... Sección: ...)
                sanitized = sanitize_text(raw_translation)
                translated_title, translated_body, translated_section = None, None, None
                try:
                    title_match = re.search(r'T[ií]tulo:([^\n]*)', sanitized, re.IGNORECASE)
                    body_match = re.search(r'Cuerpo:([^\n]*)', sanitized, re.IGNORECASE)
                    section_match = re.search(r'Secci[oó]n:([^\n]*)', sanitized, re.IGNORECASE)
                    translated_title = title_match.group(1).strip() if title_match else ''
                    translated_body = body_match.group(1).strip() if body_match else ''
                    translated_section = section_match.group(1).strip() if section_match else ''
                except Exception as e:
                    print(f"DEBUG: Parsing failed with error: {e}")
                    translated_title = sanitized
                    translated_body = ''
                    translated_section = ''
                # For plain text, sanitize all fields
                translated_title = sanitize_text(translated_title)
                translated_body = sanitize_text(translated_body)
                translated_section = sanitize_text(translated_section)
            print("==="*40)
            print(f"DEBUG: BEFORE RETURN TO CRM, Final translated fields")
            print(f"DEBUG- Title: {translated_title}, ")
            print(f"DEBUG- Body: {translated_body}, ")
            print(f"DEBUG- Section: {translated_section}")
            print("==="*40)

            # Return a real dict for translated_text
            return TranslationResponse(
                translated_text={
                    "title": translated_title,
                    "body": translated_body,
                    "section": translated_section
                },
                success=True,
                model_used=model_used
            )
        except Exception:
            return TranslationResponse(
                translated_text={
                    "title": "",
                    "body": "",
                    "section": ""
                },
                success=False,
                model_used=model_used
            )


# Global service instance
translation_service = TranslationService()