"""
Translation service for handling business logic
Coordinates between authentication, text processing, and Ollama communication
"""
from utils.generate_translation import ollama_service
from utils.sanitize_text import sanitize_text
from utils.create_prompt_translation import create_prompt_translation
from schemas.translation import TranslationRequest, TranslationResponse


class TranslationService:
    """Service class for handling translation business logic"""
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Process translation request with HTML content preservation
        
        Args:
            request: Translation request data
            
        Returns:
            Translation response with HTML structure preserved
            
        Raises:
            Exception: If translation fails
        """
        try:
            # Check if content contains HTML tags
            has_html = any('<' in text and '>' in text for text in [request.title, request.body, request.section])
            
            if has_html:
                # Use HTML-aware translation
                translated_title = await ollama_service.translate_html_content(
                    request.title, request.target_language, request.model
                )
                translated_body = await ollama_service.translate_html_content(
                    request.body, request.target_language, request.model
                )
                translated_section = await ollama_service.translate_html_content(
                    request.section, request.target_language, request.model
                )
                
                # Combine results preserving HTML structure
                final_translation = f"Título: {translated_title} Cuerpo: {translated_body} Sección: {translated_section}"
            else:
                # Use traditional text-based translation for plain text
                # Sanitize input text
                sanitized_title = sanitize_text(request.title)
                sanitized_body = sanitize_text(request.body)
                sanitized_section = sanitize_text(request.section)
                sanitized_target_language = sanitize_text(request.target_language)

                # Create structured prompt
                prompt = create_prompt_translation(
                    title=sanitized_title,
                    body=sanitized_body,
                    section=sanitized_section,
                    target_language=sanitized_target_language
                )
                
                # Get translation from Ollama
                raw_translation = await ollama_service.generate_translation(
                    prompt=prompt,
                    model=request.model
                )
                
                # Sanitize the response
                final_translation = sanitize_text(raw_translation)
            
            return TranslationResponse(
                translated_text=final_translation,
                success=True,
                model_used=request.model
            )
            
        except Exception as e:
            # Return error response
            return TranslationResponse(
                translated_text=f"Translation failed: {str(e)}",
                success=False,
                model_used=request.model
            )


# Global service instance
translation_service = TranslationService()
