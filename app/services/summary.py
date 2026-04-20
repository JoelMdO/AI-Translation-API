"""
Content sumarization service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
# import re

# from app.utils.sanitize_html import sanitize_html
# from app.utils.sanitize_text import sanitize_text
# from app.utils.summary.summary_article import summary_utils
# from app.utils.rag_service.build_context import build_context_block
# from app.schemas.translation import ResumeRequest, ResumeResponse
# from app.config import OLLAMA_BACKUP_MODEL, OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
##//TODO remove the app. before deploying 
from utils.sanitize_html import sanitize_html
from utils.sanitize_text import sanitize_text
from utils.summary.summary_article import summary_utils
from utils.rag_service.build_context import build_context_block
from schemas.translation import ResumeRequest, ResumeResponse
from config import OLLAMA_BACKUP_MODEL, OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class SummaryService:
    """Service class for handling summarization business logic"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 60.0
        self.model = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL  # Fallback if env var is not set
    async def summarize(self, request: ResumeRequest) -> ResumeResponse:
        """
        Process resume request with HTML content preservation
        Returns an object with summarized fields, avoids multiple Ollama calls if possible.
        """
        if self.model is None:
            raise RuntimeError("OLLAMA_MODEL is not configured. Set OLLAMA_BASE_URL in config.")
        
        model: str = self.model

        async def summarize_field(title: str , body: str, language: str, context_block: str = "") -> str:
            summary = await summary_utils.resume_article(
                title=title, body=body, model=model, language=language,
                context_block=context_block,
            )
            return sanitize_text(summary)
            
        try:
            # Build RAG context block (gracefully empty when ChromaDB unavailable)
            context_block = await build_context_block(request.title, request.language)
            if context_block:
                print("DEBUG: RAG context block injected into resume prompt")
            else:
                print("DEBUG: No RAG context available, proceeding without enrichment")

            has_html = any('<' in text and '>' in text for text in [request.title, request.body])
            print(f"DEBUG: has_html = {has_html}")
            if has_html:
                request.title = sanitize_html(request.title)
                request.body = sanitize_html(request.body)
                print(f"DEBUG: Resume sections after sanitize: {request.title}, body {request.body}")
                # If HTML, translate each field separately (Ollama likely needs to preserve tags)
                resume_article = await summarize_field(title=request.title, body=request.body, language=request.language, context_block=context_block)
                print(f"DEBUG: Resume sections after summarize: {resume_article}")

            else:
                # If no HTML, sanitize and process normally
                print(f"DEBUG: Resume sections no html before summarize: title={request.title}, body={request.body}")
                resume_article = await summarize_field(title=request.title, body=request.body, language=request.language, context_block=context_block)
                print(f"DEBUG: Resume sections no html: {resume_article}")
               
            # Return a real dict for translated_text
            print(f"DEBUG: Resume successful: article_sanitized={resume_article}")
            return ResumeResponse(
                article=resume_article,
                success=True,
            )
        except Exception:
            return ResumeResponse(
                article="Error during resume generation.",
                success=False,
            )
         
# Global service instance
summary_service = SummaryService()
