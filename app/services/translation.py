"""
Translation service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
from utils.sanitize_html import sanitize_html
from utils.sanitize_text import sanitize_text
from utils.ollama_services import ollama_service
from utils.create_prompt_translation import create_prompt_translation
from schemas.translation import TranslationRequest, TranslationResponse
import re
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
        try:
            # import json
            # def sanitize_html(html: str) -> str:
            #     # Remove <script> and other dangerous tags, but keep safe HTML structure
            #     # Simple regex-based removal for <script> and event handlers
            #     html = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', html, flags=re.DOTALL|re.IGNORECASE)
            #     # Remove on* event handlers (e.g., onclick, onerror)
            #     html = re.sub(r'on\w+\s*=\s*"[^"]*"', '', html, flags=re.IGNORECASE)
            #     html = re.sub(r'on\w+\s*=\s*\'[^\']*\'', '', html, flags=re.IGNORECASE)
            #     html = re.sub(r'on\w+\s*=\s*[^ >]+', '', html, flags=re.IGNORECASE)
            #     # Remove javascript: in href/src
            #     html = re.sub(r'(href|src)\s*=\s*"javascript:[^"]*"', '', html, flags=re.IGNORECASE)
            #     html = re.sub(r'(href|src)\s*=\s*\'javascript:[^\']*\'', '', html, flags=re.IGNORECASE)
            #     return html

            has_html = any('<' in text and '>' in text for text in [request.title, request.body, request.section])
            if has_html:
                # If HTML, translate each field separately (Ollama likely needs to preserve tags)
                translated_title = await ollama_service.translate_html_content(
                    request.title, request.target_language, request.model
                )
                translated_body = await ollama_service.translate_html_content(
                    request.body, request.target_language, request.model
                )
                translated_section = await ollama_service.translate_html_content(
                    request.section, request.target_language, request.model
                )
                # Sanitize only for malicious content, not for structure
                translated_title = sanitize_text(translated_title)
                translated_body = sanitize_html(translated_body)
                translated_section = sanitize_text(translated_section)
            else:
                # For plain text, sanitize and combine into a single prompt for one Ollama call
                sanitized_title = sanitize_text(request.title)
                sanitized_body = sanitize_text(request.body)
                sanitized_section = sanitize_text(request.section)
                sanitized_target_language = sanitize_text(request.target_language)

                prompt = create_prompt_translation(
                    title=sanitized_title,
                    body=sanitized_body,
                    section=sanitized_section,
                    target_language=sanitized_target_language
                )
                print(f"DEBUG: Generated prompt for translation: {prompt}")
                # Get translation from Ollama (single call)
                raw_translation = await ollama_service.generate_translation(
                    prompt=prompt,
                    model=request.model
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

            # Return a real dict for translated_text
            return TranslationResponse(
                translated_text={
                    "title": translated_title,
                    "body": translated_body,
                    "section": translated_section
                },
                success=True,
                model_used=request.model
            )
        except Exception:
            return TranslationResponse(
                translated_text={
                    "title": "",
                    "body": "",
                    "section": ""
                },
                success=False,
                model_used=request.model
            )


# Global service instance
translation_service = TranslationService()
