"""
Translation service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
from config import OLLAMA_DEFAULT_MODEL
from utils.sanitize_html import sanitize_html
from utils.sanitize_text import sanitize_text
from utils.translation.translate_html_content import translateHTMLContent
from schemas.translation import TranslatedText, TranslationRequest, TranslationResponse
import logging
from fastapi import status
# 1. Configure the logger to accept INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        model_used: str = OLLAMA_DEFAULT_MODEL or "llama3.2"
        logger.info("Translation request received with model: %s", model_used)
        print(f"====/// STARTING TRANSLATION SERVICE ///====")
        try:
            title_has_html = '<' in request.title and '>' in request.title
            print(f"Title has HTML: {title_has_html}")
            if title_has_html:
                            sanitized_title = sanitize_html(request.title)
                            translated_title = await translateHTMLContent.translate_html_content(
                                    content=sanitized_title, target_language=request.target_language
                            )
            else:
                            sanitized_title = sanitize_text(request.title)
                            translated_title = await translateHTMLContent.translate_plain_text(
                                    text=sanitized_title, target_language=request.target_language
                            )
            body_has_html  = '<' in request.body  and '>' in request.body
            print(f"Body has HTML: {body_has_html}")
            if body_has_html:

                            sanitized_body = sanitize_html(request.body)
                            translated_body = await translateHTMLContent.translate_html_content(
                                content=sanitized_body, target_language=request.target_language
                            )
            else:
                            sanitized_body = sanitize_text(request.body)
                            translated_body = await translateHTMLContent.translate_plain_text(
                                text=sanitized_body, target_language=request.target_language
                            )
            section_has_html = '<' in request.section and '>' in request.section
            print(f"Section has HTML: {section_has_html}")
            if section_has_html:
                            sanitized_section = sanitize_html(request.section)
                            translated_section = await translateHTMLContent.translate_html_content(
                                    content=sanitized_section, target_language=request.target_language
                                )
            else:
                            sanitized_section = sanitize_text(request.section)
                            print(f"//SECTION Sanitized section: {sanitized_section}")
                            translated_section = await translateHTMLContent.translate_plain_text(
                                text=sanitized_section, target_language=request.target_language
                            )
                            print(f"Translated section: {translated_section}")
 
            print(f"Final translated fields -- Title: {translated_title}")
            print(f"Final translated fields -- Body: {translated_body}")
            print(f"Final translated fields -- Section: {translated_section}")

            # UPDATED — validate and normalize mixed string/segment fields explicitly.
            translated_text = TranslatedText.model_validate(
                {
                    "title": translated_title,
                    "body": translated_body,
                    "section": translated_section,
                }
            )
            return TranslationResponse(
                translated_text=translated_text,
                status=status.HTTP_200_OK,
                model_used=model_used,
            )
        except Exception:
            logger.exception("Translation failed")
            return TranslationResponse(
                translated_text=TranslatedText(
                    title="",
                    body="",
                    section="",
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                model_used=model_used,
            )

# Global service instance
translation_service = TranslationService()
