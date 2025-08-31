"""
Content sumarization service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
# import re

from app.utils.sanitize_html import sanitize_html
from app.utils.ollama_services import ollama_service
from app.utils.sanitize_text import sanitize_text
from app.schemas.translation import ResumeRequest, ResumeResponse
from app.config import OLLAMA_DEFAULT_MODEL
##//TODO change by removing app before deploying 
# from utils.sanitize_html import sanitize_html
# from utils.ollama_services import ollama_service
# from utils.sanitize_text import sanitize_text
# from schemas.translation import ResumeRequest, ResumeResponse
# from config import OLLAMA_DEFAULT_MODEL

class ResumeService:
    """Service class for handling summarization business logic"""

    async def summarize(self, request: ResumeRequest) -> ResumeResponse:
        """
        Process resume request with HTML content preservation
        Returns an object with summarized fields, avoids multiple Ollama calls if possible.
        """

        async def summarize_field(text: str , language: str) -> str:
            summary = await ollama_service.resume_article(
                request=text, model=OLLAMA_DEFAULT_MODEL or "llama3.2", language=language
            )
            return sanitize_text(summary)
        
        resume_article = ""
        resume_es_article = ""
        
        try:
     
            has_html = any('<' in text and '>' in text for text in [request.article, request.esArticle])
            print(f"DEBUG: has_html = {has_html}")
            print(f"DEBUG: Article", request.article)
            print(f"DEBUG: Article (ES)", request.esArticle)
            if has_html:
                request.article = sanitize_html(request.article)
                request.esArticle = sanitize_html(request.esArticle)
                print(f"DEBUG: Resume sections after sanitize: {request.article}, esArticle {request.esArticle}")
                # If HTML, translate each field separately (Ollama likely needs to preserve tags)
                resume_article = await summarize_field(request.article, language="en")
                resume_es_article = await summarize_field(request.esArticle, language="es")
                print(f"DEBUG: Resume sections after summarize: {resume_article}, esArticle {resume_es_article}")

            else:
                # If no HTML, sanitize and process normally
                resume_article = await summarize_field(request.article, language="en")
                resume_es_article = await summarize_field(request.esArticle, language="es")
                print(f"DEBUG: Resume sections no html: {resume_article}")
               
            # Return a real dict for translated_text
            print(f"DEBUG: Resume successful: article_sanitized={resume_article}, article_es_sanitized={resume_es_article}")
            return ResumeResponse(
                article=resume_article,
                esArticle=resume_es_article
            )
        except Exception:
            return ResumeResponse(
                article="",
                esArticle=""
            )
         
# Global service instance
resume_service = ResumeService()
