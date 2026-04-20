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
import logging

logger = logging.getLogger(__name__)

##//TODO remove app before deploying 
# from app.config import OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
# from app.utils.sanitize_html import sanitize_html
# from app.utils.sanitize_text import sanitize_text
# from app.utils.translation.translate_html_content import translateHTMLContent
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
        logger.info("Translation request received with model: %s", model_used)
        try:
            title_has_html = '<' in request.title and '>' in request.title
            logger.info("Title has HTML: %s", title_has_html)
            body_has_html  = '<' in request.body  and '>' in request.body
            logger.info("Body has HTML: %s", body_has_html)
            section_has_html = '<' in request.section and '>' in request.section
            logger.info("Section has HTML: %s", section_has_html)
            any_has_html = title_has_html or body_has_html or section_has_html
            logger.info("Translation request received. title_has_html=%s body_has_html=%s section_has_html=%s",
                    title_has_html, body_has_html, section_has_html)
            if any_has_html:
                # Per-field routing: HTML fields use HTML translation, plain-text fields use plain translation
                if title_has_html:
                    translated_title = sanitize_html(
                        await translateHTMLContent.translate_html_content(
                            content=request.title, target_language=request.target_language
                        )
                    )
                else:
                    translated_title = sanitize_text(
                        await translateHTMLContent.translate_plain_text(
                            text=request.title, target_language=request.target_language
                        )
                    )

                if body_has_html:
                    logger.info("Translating body with HTML preservation")
                    translated_body = sanitize_html(
                        await translateHTMLContent.translate_html_content(
                            content=request.body, target_language=request.target_language
                        )
                    )
                else:
                    logger.info("Translating body as plain text")
                    translated_body = sanitize_text(
                        await translateHTMLContent.translate_plain_text(
                            text=request.body, target_language=request.target_language
                        )
                    )

                if section_has_html:
                    translated_section = sanitize_html(
                        await translateHTMLContent.translate_html_content(
                            content=request.section, target_language=request.target_language
                        )
                    )
                else:
                    translated_section = sanitize_text(
                        await translateHTMLContent.translate_plain_text(
                            text=request.section, target_language=request.target_language
                        )
                    )

                logger.info("Translated title length: %d", len(translated_title or ""))
                logger.info("Translated body length: %d", len(translated_body or ""))
                logger.info("Translated section length: %d", len(translated_section or ""))
            else:
                # For plain text, sanitize and combine into a single prompt for one Ollama call
                logger.info("No HTML detected in any field; using single translation call for efficiency")
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
                logger.info("Raw translation response: %s", raw_translation)
                # Try to parse the response into fields (assuming format: Título: ... Cuerpo: ... Sección: ...)
                sanitized = sanitize_text(raw_translation)
                translated_title, translated_body, translated_section = None, None, None
                try:
                    # Support multi-line fields by using DOTALL and non-greedy matches
                    title_match = re.search(
                        r"T[ií]tulo:\s*(.*?)(?=Cuerpo:|Secci[oó]n:|$)",
                        sanitized,
                        re.IGNORECASE | re.DOTALL,
                    )
                    body_match = re.search(
                        r"Cuerpo:\s*(.*?)(?=Secci[oó]n:|$)",
                        sanitized,
                        re.IGNORECASE | re.DOTALL,
                    )
                    section_match = re.search(
                        r"Secci[oó]n:\s*(.*)$",
                        sanitized,
                        re.IGNORECASE | re.DOTALL,
                    )
                    translated_title = title_match.group(1).strip() if title_match else ''
                    translated_body = body_match.group(1).strip() if body_match else ''
                    translated_section = section_match.group(1).strip() if section_match else ''
                except Exception:
                    logger.exception("Parsing raw translation failed; falling back to whole text")
                    translated_title = sanitized
                    translated_body = ''
                    translated_section = ''
                # For plain text, sanitize all fields
                translated_title = sanitize_text(translated_title)
                translated_body = sanitize_text(translated_body)
                translated_section = sanitize_text(translated_section)
            logger.info("Final translated fields -- Title: %s", translated_title)
            logger.info("Final translated fields -- Body length: %d", len(translated_body or ""))
            logger.info("Final translated fields -- Section: %s", translated_section)

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
            logger.exception("Translation failed for request: %s", request)
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