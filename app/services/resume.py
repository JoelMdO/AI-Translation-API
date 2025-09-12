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

        async def summarize_field(title: str , body: str, language: str) -> str:
            summary = await ollama_service.resume_article(
                title=title, body=body, model=OLLAMA_DEFAULT_MODEL or "llama3.2", language=language
            )
            return sanitize_text(summary)
            
        try:
            has_html = any('<' in text and '>' in text for text in [request.title, request.body])
            print(f"DEBUG: has_html = {has_html}")
            if has_html:
                request.title = sanitize_html(request.title)
                request.body = sanitize_html(request.body)
                print(f"DEBUG: Resume sections after sanitize: {request.title}, body {request.body}")
                # If HTML, translate each field separately (Ollama likely needs to preserve tags)
                resume_article = await summarize_field(title=request.title, body=request.body, language=request.language)
                print(f"DEBUG: Resume sections after summarize: {resume_article}")

            else:
                # If no HTML, sanitize and process normally
                print(f"DEBUG: Resume sections no html before summarize: title={request.title}, body={request.body}")
                resume_article = await summarize_field(title=request.title, body=request.body, language=request.language)
                print(f"DEBUG: Resume sections no html: {resume_article}")
               
            # Return a real dict for translated_text
            print(f"DEBUG: Resume successful: article_sanitized={resume_article}")
            return ResumeResponse(
                article=resume_article,
                success=True,
            )
        except Exception as e:
            return ResumeResponse(
                article=f"Error during resume generation: {str(e)}",
                success=False,
            )
         
# Global service instance
resume_service = ResumeService()
